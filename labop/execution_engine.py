import datetime
import logging
import os
import uuid
from abc import ABC
from typing import Callable, Dict, List, Union
from urllib.parse import quote, unquote

import pandas as pd
import sbol3

from labop.behavior_execution import BehaviorExecution
from labop_convert import DefaultBehaviorSpecialization
from uml import ActivityNode, CallBehaviorAction
from uml.activity_edge import ActivityEdge
from uml.activity_parameter_node import ActivityParameterNode
from uml.literal_specification import LiteralSpecification
from uml.utils import literal

from .activity_edge_flow import ActivityEdgeFlow
from .activity_node_execution import ActivityNodeExecution
from .call_behavior_execution import CallBehaviorExecution
from .dataset import Dataset
from .parameter_value import ParameterValue
from .primitive import Primitive
from .protocol import Protocol
from .protocol_execution import ProtocolExecution
from .sample_data import SampleData

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


failsafe = True  # When set to True, a protocol execution will proceed through to the end, even if a CallBehaviorAction raises an exception.  Set to False for debugging


class ExecutionError(Exception):
    pass


class ExecutionWarning(Exception):
    pass


class ExecutionEngine(ABC):
    """Base class for implementing and recording a LabOP executions.
    This class can handle common UML activities and the propagation of tokens, but does not execute primitives.
    It needs to be extended with specific implementations that have that capability.
    """

    def __init__(
        self,
        specializations=[DefaultBehaviorSpecialization()],
        use_ordinal_time=False,
        failsafe=True,
        permissive=False,
        use_defined_primitives=True,
        sample_format="xarray",
        out_dir="out",
        dataset_file=None,
    ):
        self.exec_counter = 0
        self.variable_counter = 0
        self.specializations = specializations

        # The EE uses a configurable start_time as the reference time.
        # Because the start_time is not always the actual time, then
        # we need to set times relative to the start time using the
        # relative wall clock time.
        # if use_oridinal_time, then use a new int for each time
        self.start_time = None  # The official start_time
        self.wall_clock_start_time = None  # The actual now() time
        self.use_ordinal_time = use_ordinal_time  # Use int instead of datetime
        self.ordinal_time = None
        self.current_node = None
        self.blocked_nodes = set({})
        self.tokens = []  # no tokens to start
        self.ex = None
        self.is_asynchronous = True
        self.failsafe = failsafe
        self.permissive = permissive  # Allow execution to follow control flow even if objects not present.
        self.use_defined_primitives = use_defined_primitives  # used the compute_output definitions to compute primitive outputs
        self.sample_format = sample_format
        self.issues: Dict[
            id, List[Union[ExecutionWarning, ExecutionError]]
        ] = {}  # List of Warnings and Errors
        self.out_dir = out_dir
        self.dataset_file = dataset_file  # Write dataset specifications as template files used to fill in data
        self.data_id = 0
        self.data_id_map = {}
        self.candidate_clusters = {}
        self.incoming_edge_tokens = {}  # Maps node -> edge -> value

    def next_id(self):
        next = self.exec_counter
        self.exec_counter += 1
        return next

    def next_variable(self):
        variable = f"var_{self.variable_counter}"
        self.variable_counter += 1
        return variable

    def init_time(self, start_time):
        self.wall_clock_start_time = datetime.datetime.now()
        if self.use_ordinal_time:
            self.ordinal_time = datetime.datetime.strptime(
                "1/1/00 00:00:00", "%d/%m/%y %H:%M:%S"
            )
            self.start_time = self.ordinal_time
        else:
            start_time = start_time if start_time else datetime.datetime.now()
            self.start_time = start_time

    def get_current_time(self, as_string=False):
        if self.use_ordinal_time:
            now = self.ordinal_time
            self.ordinal_time += datetime.timedelta(seconds=1)
            start = self.start_time
        else:
            now = datetime.datetime.now()
            start = self.wall_clock_start_time

        # get the relative time from start
        rel_start = now - start
        cur_time = self.start_time + rel_start
        return cur_time if not as_string else str(cur_time)

    def initialize(
        self,
        protocol: Protocol,
        agent: sbol3.Agent,
        id: str = uuid.uuid4(),
        parameter_values: List[ParameterValue] = {},
    ):
        # Record in the document containing the protocol
        doc = protocol.document

        # setup possible issues
        self.issues[id] = []

        if self.use_defined_primitives:
            # Define the compute_output function for known primitives
            Primitive.initialize_primitive_compute_output(doc)

        # First, set up the record for the protocol and parameter values
        self.ex = ProtocolExecution(id, protocol=protocol)
        doc.add(self.ex)

        self.ex.association.append(sbol3.Association(agent=agent, plan=protocol))
        self.ex.parameter_values = parameter_values

        # Setup incoming edge map for each node
        for node in protocol.nodes:
            for e in protocol.incoming_edges(node):
                self.incoming_edge_tokens[node][e] = []
            if isinstance(node, ActivityParameterNode) and node.input():
                # if matching input parameters, then add dummy edge value
                param_values = [
                    pv
                    for pv in self.ex.parameter_values
                    if pv.parameter() == node.parameter()
                ]
                for pv in param_values:
                    self.incoming_edge_tokens[node][pv.parameter()] = pv.value()

        # Initialize specializations
        for specialization in self.specializations:
            specialization.initialize_protocol(self.ex, out_dir=self.out_dir)
            specialization.on_begin(self.ex)

    def finalize(
        self,
        protocol: Protocol,
    ):
        self.ex.end_time = self.get_current_time()

        # A Protocol has completed normally if all of its required output parameters have values
        self.ex.completed_normally = set(protocol.get_required_inputs()).issubset(
            set([p.parameter.lookup() for p in self.ex.parameter_values])
        )

        # aggregate consumed material records from all behaviors executed within, mark end time, and return
        self.ex.aggregate_child_materials()

        # End specializations
        for specialization in self.specializations:
            specialization.on_end(self.ex)

    def execute(
        self,
        protocol: Protocol,
        agent: sbol3.Agent,
        parameter_values: List[ParameterValue] = {},
        id: str = uuid.uuid4(),
        start_time: datetime.datetime = None,
    ) -> ProtocolExecution:
        """Execute the given protocol against the provided parameters

        Parameters
        ----------
        protocol: Protocol to execute
        agent: Agent that is executing this protocol
        parameter_values: List of all input parameter values (if any)
        id: display_id or URI to be used as the name of this execution; defaults to a UUID display_id
        start_time: Start time for the execution

        Returns
        -------
        ProtocolExecution containing a record of the execution
        """

        self.initialize(protocol, agent, id, parameter_values)
        self.run(protocol, start_time=start_time)
        self.finalize(protocol)

        return self.ex

    def run(self, protocol: Protocol, start_time: datetime.datetime = None):
        self.init_time(start_time)
        self.ex.start_time = (
            self.start_time
        )  # TODO: remove str wrapper after sbol_factory #22 fixed

        ready = protocol.initiating_nodes()

        # Iteratively execute all unblocked activities until no more tokens can progress
        while ready:
            ready = self.step(ready)
        return ready

    def step(
        self,
        ready: List[ActivityNode],
        node_outputs: Dict[ActivityNode, Callable] = {},
    ):
        non_call_nodes = [
            node for node in ready if not isinstance(node, CallBehaviorAction)
        ]
        new_tokens = []
        # prefer executing non_call_nodes first
        for node in non_call_nodes + [n for n in ready if n not in non_call_nodes]:
            self.current_node = node
            try:
                calling_behaviors = self.possible_calling_behaviors(node)
                outgoing_edges = self.ex.protocol.outgoing_edges(node)
                node.consume_tokens()
                tokens_added, tokens_removed = node.execute(
                    self.incoming_edge_tokens[node],
                    outgoing_edges,
                    (node_outputs[node] if node in node_outputs else None),
                    calling_behaviors,
                    self.sample_format,
                    self.permissive,
                )

                consumed_tokens = self.consume_tokens(tokens_removed)
                self.tokens = [t for t in self.tokens if t not in consumed_tokens]
                record = self.create_record(node, consumed_tokens)

                self.ex.executions.append(record)

                tokens_added = [
                    ActivityEdgeFlow(edge=edge, token_source=node, value=value)
                    for edge, value in tokens_added.items()
                ]
                self.ex.flows += tokens_added
                new_tokens = new_tokens + tokens_added

                self.post_process(record, tokens_added)

            except Exception as e:
                # Consume the tokens used by the node that caused the exception
                # Produce control tokens
                # incoming_flows = [
                #     t for t in self.tokens if node == t.get_target()
                # ]
                # exec = CallBehaviorExecution(
                #     node=node, incoming_flows=incoming_flows
                # )
                # self.ex.document.add(exec)
                # self.ex.executions.append(exec)
                # control_edges = [
                #     edge
                #     for edge in self.ex.protocol.lookup().edges
                #     if (
                #         node.identity == edge.source
                #         or node.identity
                #         == edge.source.lookup().get_parent().identity
                #     )
                #     and (isinstance(edge, ControlFlow))
                # ]

                # self.tokens = [
                #     t for t in self.tokens if t.get_target() != node
                # ] + [
                #     ActivityEdgeFlow(
                #         token_source=exec,
                #         edge=edge,
                #         value=literal("uml.ControlFlow"),
                #     )
                #     for edge in control_edges
                # ]
                if self.permissive:
                    self.issues[self.ex.display_id].append(ExecutionWarning(e))
                else:
                    self.issues[self.ex.display_id].append(ExecutionError(e))
                    raise (e)
        self.tokens = self.tokens + new_tokens
        return self.executable_activity_nodes(new_tokens)

    def possible_calling_behaviors(self, node: ActivityNode):
        # Get all CallBehaviorAction nodes that correspond to a CallBehaviorExecution that supports the current execution of the ActivityNode
        tokens_supporting_node = [
            t for t in self.tokens if t.edge in self.incoming_edge_tokens[node]
        ]
        records = set(
            [t.source.get_calling_behavior_execution() for t in tokens_supporting_node]
        )
        nodes = set({record.node for record in records})
        return nodes

    def create_record(self, node, consumed_tokens):
        if isinstance(node, CallBehaviorAction):
            call = BehaviorExecution(
                f"execute_{self.next_id()}",
                parameter_values=self.record_parameter_values(node, consumed_tokens),
                completed_normally=True,
                start_time=self.get_current_time(),  # TODO: remove str wrapper after sbol_factory #22 fixed
                end_time=self.get_current_time(),  # TODO: remove str wrapper after sbol_factory #22 fixed
                consumed_material=[],
            )  # FIXME handle materials
            record = CallBehaviorExecution(
                node=node, incoming_flows=consumed_tokens, call=call
            )
            self.ex.document.add(call)
        else:
            record = ActivityNodeExecution(node=node, incoming_flows=consumed_tokens)
        return record

    def record_parameter_values(
        self, node: CallBehaviorAction, inputs: List[ActivityEdgeFlow]
    ) -> List[ParameterValue]:
        # Get the parameter values from input tokens for input pins
        input_pin_values = {
            token.token_source.lookup()
            .node.lookup()
            .identity: literal(token.value, reference=True)
            for token in inputs
            if not token.edge
        }
        # Get Input value pins
        value_pin_values = {}

        # Validate Pin values, see #130
        # Although enabled_activity_node method also validates Pin values,
        # it only checks required Pins.  This check is necessary to check optional Pins.
        for pin in self.inputs:
            if hasattr(pin, "value"):
                if pin.value is None:
                    raise ValueError(
                        f"{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}"
                    )
                value_pin_values[pin.identity] = pin.value
            # Check that pin corresponds to an input parameter.  Will cause Exception if does not exist.
            parameter = self.pin_parameter(pin.name)

        # Convert References
        value_pin_values = {
            k: literal(value=v.get_value(), reference=True)
            for k, v in value_pin_values.items()
        }
        pin_values = {**input_pin_values, **value_pin_values}  # merge the dicts

        parameter_values = [
            ParameterValue(
                parameter=self.pin_parameter(pin.name),
                value=pin_values[pin.identity],
            )
            for pin in self.inputs
            if pin.identity in pin_values
        ]
        return parameter_values

    def consume_tokens(
        self,
        node: ActivityNode,
        tokens_removed: Dict[ActivityEdge, LiteralSpecification],
    ) -> List[ActivityEdgeFlow]:
        consumed_tokens = [
            t
            for t in self.tokens
            if t.edge in tokens_removed and tokens_removed[t.edge] == t.value
        ]

        # Remove values on edges
        self.incoming_edge_tokens[node] = {
            edge: [
                v
                for v in self.incoming_edge_tokens[node][edge]
                if v != tokens_removed[edge]
            ]
            for edge in self.incoming_edge_tokens[node]
        }
        return consumed_tokens

    def executable_activity_nodes(self, tokens_added) -> List[ActivityNode]:
        """Find all of the activity nodes that are ready to be run given the current set of tokens
        Note that this will NOT identify activities with no in-flows: those are only set up as initiating nodes

        Parameters
        ----------

        Returns
        -------
        List of ActivityNodes that are ready to be run
        """
        # candidate_clusters = {}
        updated_clusters = set({})
        for t in tokens_added:
            target = t.get_target()
            self.incoming_edge_tokens[target][t.edge].append(t.value)
            self.candidate_clusters[target.identity] = self.candidate_clusters.get(
                target.identity, []
            ) + [t]
            updated_clusters.add(target)

        enabled_nodes = [
            n
            for n in updated_clusters
            if n.enabled(
                self,
                self.incoming_edge_tokens[n],
                permissive=self.permissive,
            )
        ]
        enabled_nodes.sort(
            key=lambda x: x.identity
        )  # Avoid any ordering non-determinism

        return enabled_nodes

    def post_process(
        self,
        record: ActivityNodeExecution,
        new_tokens: List[ActivityEdgeFlow],
    ):
        node = record.node()
        if isinstance(node, ActivityParameterNode) and node.parameter().output():
            self.ex.parameter_values += [
                ParameterValue(
                    parameter=node.parameter(),
                    value=literal(node.value(), reference=True),
                )
            ]

            # Activity Call Edges
            self.ex.activity_call_edge += [
                token.edge
                for token in new_tokens
                if token.edge not in node.protocol().edges
            ]

        if self.dataset_file is not None:
            self.write_data_templates(record, new_tokens)

        for specialization in self.specializations:
            try:
                specialization.process(record, self.ex)
            except Exception as e:
                if not self.failsafe:
                    raise e
                l.error(
                    f"Could Not Process {record.name if record.name else record.identity}: {e}"
                )

    def write_data_templates(
        self,
        record: ActivityNodeExecution,
        new_tokens: List[ActivityEdgeFlow],
    ):
        """
        Write a data template as an xlsx file if the record.node produces sample data (i.e., it has an output of type Dataset with a data attribute of type SampleData)
        Parameters
        ----------
        node : ActivityNodeExecution
            ActivityNodeExecution that produces SampleData
        """
        if not isinstance(record, CallBehaviorExecution):
            return

        # Find all Dataset objects produced by record
        datasets = [
            token.value.get_value()
            for token in new_tokens
            if token.token_source == record.identity
            and isinstance(token.value.get_value(), Dataset)
        ]
        sample_data = [
            dataset.data for dataset in datasets if isinstance(dataset.data, SampleData)
        ]

        path = os.path.join(self.out_dir, f"{self.dataset_file}.xlsx")

        for dataset in datasets:
            sheet_name = f"{record.node.lookup().behavior.lookup().display_id}_dataset_{self.data_id}"
            dataset.update_data_sheet(
                path, sheet_name, sample_format=self.sample_format
            )
            self.data_id += 1

        for sd in sample_data:
            sheet_name = f"{record.node.lookup().behavior.lookup().display_id}_data_{self.data_id}"
            sd.update_data_sheet(path, sheet_name, sample_format=self.sample_format)
            self.data_id += 1


class ManualExecutionEngine(ExecutionEngine):
    def run(self, protocol: Protocol, start_time: datetime.datetime = None):
        self.init_time(start_time)
        self.ex.start_time = (
            self.start_time
        )  # TODO: remove str wrapper after sbol_factory #22 fixed
        ready = protocol.initiating_nodes()
        ready = self.advance(ready)
        choices = self.ready_message(ready)
        graph = self.ex.to_dot(
            ready=ready, done=self.ex.backtrace()[0], out_dir=self.out_dir
        )
        return ready, choices, graph

    def advance(self, ready: List[ActivityNode]):
        def auto_advance(r):
            # If Node is a CallBehavior action, then:
            if isinstance(r, CallBehaviorAction):
                behavior = r.behavior.lookup()
                return (  # It is a subprotocol
                    isinstance(behavior, Protocol)
                    or (len(list(behavior.get_outputs())) == 0)  # Has no output pins
                    or (  # Overrides the (empty) default implementation of compute_output()
                        not hasattr(behavior.compute_output, "__func__")
                        or behavior.compute_output.__func__ != Primitive.compute_output
                    )
                )
            else:
                return True

        auto_advance_nodes = [r for r in ready if auto_advance(r)]

        while len(auto_advance_nodes) > 0:
            ready = self.step(auto_advance_nodes)
            auto_advance_nodes = [r for r in ready if auto_advance(r)]

        return self.executable_activity_nodes()

    def ready_message(self, ready: List[ActivityNode]):
        msg = "Activities Ready to Execute:\n"

        def activity_name(a):
            return a.display_id

        def behavior_name(a):
            return a.display_id

        def decision_name(a):
            return a.identity

        activities = [activity_name(r.protocol()) for r in ready]
        behaviors = [
            behavior_name(r.behavior.lookup())
            if isinstance(r, CallBehaviorAction)
            else decision_name(r)
            for r in ready
        ]
        identities = [r.identity for r in ready]
        choices = pd.DataFrame(
            {
                "Activity": activities,
                "Behavior": behaviors,
                "Identity": identities,
            }
        )
        # ready_nodes = "\n".join([f"{idx}: {r.behavior}" for idx, r in enumerate(ready)])
        return (
            "<div style='height: 200px; overflow: auto; width: fit-content'>"
            + choices.to_html()
            + "</div>"
        )
        # return choices #f"{msg}{ready_nodes}"

    def next(self, activity_node: ActivityNode, node_output: callable):
        """Execute a single ActivityNode using the node_output function to calculate its output pin values.

        Args:
            activity_node (ActivityNode): node to execute
            node_output (callable): function to calculate output pins

        Returns:
            _type_: _description_
        """
        successors = self.step(
            [activity_node], node_outputs={activity_node: node_output}
        )
        ready = self.advance(successors)
        choices = self.ready_message(ready)
        graph = self.ex.to_dot(ready=ready, done=self.ex.backtrace()[0])
        return ready, choices, graph


##################################
# Helper utility functions
