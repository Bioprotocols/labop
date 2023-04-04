import datetime
import logging
import os
import uuid
from abc import ABC
from typing import Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
import sbol3

from labop.behavior_execution import BehaviorExecution
from labop.execution_context import ExecutionContext
from uml import ActivityNode, CallBehaviorAction
from uml.activity import Activity
from uml.activity_edge import ActivityEdge
from uml.activity_parameter_node import ActivityParameterNode
from uml.control_flow import ControlFlow
from uml.input_pin import InputPin
from uml.object_flow import ObjectFlow
from uml.output_pin import OutputPin
from uml.pin import Pin
from uml.utils import literal
from uml.value_pin import ValuePin

from .activity_edge_flow import ActivityEdgeFlow
from .activity_node_execution import ActivityNodeExecution
from .call_behavior_execution import CallBehaviorExecution
from .dataset import Dataset
from .parameter_value import ParameterValue
from .primitive import Primitive
from .protocol import Protocol
from .protocol_execution import ProtocolExecution
from .sample_data import SampleData

l: logging.Logger = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class ExecutionError(Exception):
    pass


class ExecutionWarning(Exception):
    pass


class ExecutionEngine(ABC):
    """Base class for implementing and recording a LabOP executions.
    This class can handle common UML activities and the propagation of tokens,
    but does not execute primitives. It needs to be extended with specific
    implementations that have that capability.
    """

    def __init__(
        self,
        specializations: Optional[List["BehaviorSpecialization"]] = None,
        use_ordinal_time: bool = False,
        failsafe: bool = True,
        permissive: bool = False,
        use_defined_primitives: bool = True,
        sample_format: str = "xarray",
        out_dir: str = "out",
        dataset_file: str = None,  # type: ignore
    ):
        self.exec_counter = 0
        self.variable_counter = 0

        # Remove circular import with labop_convert
        self.specializations = specializations
        from labop_convert import DefaultBehaviorSpecialization

        if self.specializations is None:
            self.specializations = []
        if DefaultBehaviorSpecialization not in specializations:
            specializations += [DefaultBehaviorSpecialization()]

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

        self.ex = None
        self.is_asynchronous = True

        # When set to True, a protocol execution will proceed through to the end, even
        # if a CallBehaviorAction raises an exception.  Set to False for debugging
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

    def get_current_time(self, as_string: bool = False):
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
        execution_context=None,
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

        if execution_context is None:
            execution_content = ExecutionContext(self.ex, protocol, parameter_values)

        self.run(execution_content, start_time=start_time)
        self.finalize(protocol)

        return self.ex

    def run(
        self,
        execution_context: ExecutionContext,
        start_time: datetime.datetime = None,
    ):
        self.init_time(start_time)
        self.ex.start_time = (
            self.start_time
        )  # TODO: remove str wrapper after sbol_factory #22 fixed

        execution_contexts = [execution_context]

        # Iteratively execute all unblocked activities until no more tokens can progress
        while any([c.ready for c in execution_contexts]):
            execution_contexts = self.step(execution_contexts)
        return execution_contexts

    def step(
        self,
        active_contexts: List[ExecutionContext],
        node_outputs: Dict[ActivityNode, Callable] = {},
    ):
        new_execution_contexts = []
        new_tokens = {}
        for ec in active_contexts:
            new_tokens[ec] = [] if ec not in new_tokens else new_tokens[ec]
            non_call_nodes = [
                node for node in ec.ready if not isinstance(node, CallBehaviorAction)
            ]

            # prefer executing non_call_nodes first
            for node in non_call_nodes + [
                n for n in ec.ready if n not in non_call_nodes
            ]:
                self.current_node = node
                try:
                    (
                        tokens_created,
                        tokens_consumed,
                        new_execution_context,
                    ) = self.execute_node(ec, node, node_outputs)

                    ec.tokens = [t for t in ec.tokens if t not in tokens_consumed[ec]]
                    for _, created in tokens_created.items():
                        self.ex.flows += created
                    new_tokens[ec] += tokens_created[ec]

                    # new_execution_context will have tokens and ready nodes initialized
                    if new_execution_context is not None:
                        new_execution_contexts.append(new_execution_context)
                        new_tokens[new_execution_context] = tokens_created[
                            new_execution_context
                        ]

                except Exception as e:
                    if self.permissive:
                        self.issues[self.ex.display_id].append(ExecutionWarning(e))
                    else:
                        self.issues[self.ex.display_id].append(ExecutionError(e))
                        raise (e)
        active_contexts += new_execution_contexts
        for ec in active_contexts:
            ec.tokens += new_tokens[ec]
            ec.ready = self.executable_activity_nodes(ec, new_tokens[ec])

        return (
            active_contexts  # FIXME need to filter contexts that are no longer active
        )

    def execute_node(
        self,
        execution_context: ExecutionContext,
        node: ActivityNode,
        node_outputs: Dict[ActivityNode, Callable] = {},
    ) -> Tuple[
        Dict[ExecutionContext, List[ActivityEdgeFlow]],
        Dict[ExecutionContext, List[ActivityEdgeFlow]],
        ExecutionContext,
    ]:
        # Process inputs
        supporting_tokens: Dict[
            ActivityEdge, List[ActivityEdgeFlow]
        ] = execution_context.incoming_edge_tokens[node]

        tokens_consumed: Dict[
            ExecutionContext, List[ActivityEdgeFlow]
        ] = self.consume_tokens(execution_context, node, supporting_tokens)

        # Create execution record
        record = self.create_record(node, tokens_consumed[execution_context])
        self.ex.executions.append(record)

        # from ActivityNode.execute()
        tokens_created: Dict[
            ExecutionContext, List[ActivityEdgeFlow]
        ] = self.next_tokens(execution_context, record, node_outputs)

        # from ActivityNode.next_tokens()
        # self.check_next_tokens(new_tokens, node_outputs, self.sample_format, self.permissive)

        # tokens_added = [
        #     ActivityEdgeFlow(edge=edge, token_source=node, value=value)
        #     for edge, value in tokens_added.items()
        # ]

        # Side Effects / Bookkeeping
        self.post_process(execution_context, record, tokens_created[execution_context])

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
        #         == edge.get_source().get_parent().identity
        #     )
        #     and (isinstance(edge, ControlFlow))
        # ]

        # self.tokens = [
        #     t for t in self.tokens if t.get_target() != node
        # ] + [
        #     ActivityEdgeFlow(
        #         token_source=exec: ExecutionContext,
        #         edge=edge, List[ActivityEdgeFlow],
        #         value=literal("uml.ControlFlow"),
        #     )
        #     for edge in control_edges
        # ]

        new_ecs = [ec for ec in tokens_created.keys() if ec != execution_context]
        if new_ecs is not None and len(new_ecs) == 1:
            new_execution_context = next(iter(new_ecs))
        elif new_ecs is not None and len(new_ecs) > 1:
            raise Exception(
                f"Executing {node}, resulted in {len(new_ecs)} new execution context(s)."
            )
        else:
            new_execution_context = None

        return tokens_created, tokens_consumed, new_execution_context

    def next_tokens(
        self,
        execution_context: ExecutionContext,
        record: ActivityNodeExecution,
        node_outputs: Callable,
    ) -> Dict[ExecutionContext, List[ActivityEdgeFlow]]:
        # next_tokens_callback cases
        # ActivityNode: get_value(edge)
        # ActivityParameterNode: parameter-value token, input/output edges, get_value()
        # CallBehaviorAction call_subprotocol or super()
        # DecisionNode: handle input cases to pick output
        # FinalNode: handle end of protocol and return
        # ForkNode: handle in ActivityNode? copy/ref tokens
        # InputPin: handle case with no edge between pin and CallBehaviorAction
        # Process outputs
        node = record.get_node()
        outgoing_edges = execution_context.outgoing_edges(node)
        parameter_value_map = record.parameter_value_map()

        new_tokens: Dict[ExecutionContext, List[ActivityEdgeFlow]] = {
            execution_context: [
                ActivityEdgeFlow(
                    edge=edge,
                    token_source=record,
                    value=node.get_value(
                        edge,
                        parameter_value_map,
                        node_outputs,
                        self.sample_format,
                    ),
                )
                for edge in outgoing_edges
            ]
        }

        if isinstance(node, CallBehaviorAction):
            behavior = node.get_behavior()
            if isinstance(behavior, Activity):
                new_execution_context = execution_context.invoke_activity(record)

                # Create tokens that cross from parent to child context.
                # Tokens include:
                #  - parent input/value pin to child activity parameter node
                #  - parent call_behavior_action to child initial
                new_tokens[new_execution_context] = [
                    ActivityEdgeFlow(
                        edge=new_execution_context.get_invocation_edge(
                            token_consumed.get_edge().get_source(),
                        ),
                        token_source=token_consumed.token_source,
                        value=literal(token_consumed.value, reference=True),
                    )
                    for token_consumed in record.get_incoming_flows()
                    if isinstance(token_consumed.get_edge().get_source(), Pin)
                    for activity_parameter_node in behavior.get_nodes(
                        name=token_consumed.get_edge().get_source().name,
                        node_type=ActivityParameterNode,
                    )
                ] + [
                    ActivityEdgeFlow(
                        edge=new_execution_context.get_invocation_edge(
                            node, behavior.initial()
                        ),
                        token_source=record,
                        value=literal("uml.ControlFlow", reference=True),
                    )
                ]

        return new_tokens

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

    def create_record(
        self,
        node: ActivityNode,
        consumed_tokens: List[ActivityEdgeFlow],
    ) -> ActivityNodeExecution:
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
        self,
        node: CallBehaviorAction,
        inputs: Dict[ExecutionContext, List[ActivityEdgeFlow]],
    ) -> List[ParameterValue]:
        # Get the parameter values from input tokens for input pins
        input_pin_values = {
            token.token_source.lookup()
            .node.lookup()
            .identity: literal(token.value, reference=True)
            for token in inputs
        }
        # Get Input value pins
        value_pin_values = {}

        # Validate Pin values, see #130
        # Although enabled_activity_node method also validates Pin values,
        # it only checks required Pins.  This check is necessary to check optional Pins.
        for pin in node.get_inputs():
            if hasattr(pin, "value"):
                if pin.value is None:
                    raise ValueError(
                        f"{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}"
                    )
                value_pin_values[pin.identity] = pin.value
            # Check that pin corresponds to an input parameter.  Will cause Exception if does not exist.
            parameter = node.pin_parameter(pin.name)

        # Convert References
        value_pin_values = {
            k: literal(value=v.get_value(), reference=True)
            for k, v in value_pin_values.items()
        }
        pin_values = {**input_pin_values, **value_pin_values}  # merge the dicts

        parameter_values = [
            ParameterValue(
                parameter=node.pin_parameter(pin.name),
                value=pin_values[pin.identity],
            )
            for pin in node.get_inputs()
            if pin.identity in pin_values
        ]
        return parameter_values

    def consume_tokens(
        self,
        execution_context: ExecutionContext,
        node: ActivityNode,
        supporting_tokens: Dict[ActivityEdge, List[ActivityEdgeFlow]],
    ) -> Dict[ExecutionContext, List[ActivityEdgeFlow]]:
        ec_consumed_tokens = []
        for edge, tokens in supporting_tokens.items():
            source = edge.get_source()
            target = edge.get_target()
            try:
                token = next(iter(tokens))
                ec_consumed_tokens.append(token)
            except StopIteration:
                if source.required():
                    msg = f"Could not find a required token for source: {source.name}"
                    if self.permissive:
                        raise ExecutionWarning(msg)
                    else:
                        raise ExecutionError(msg)

        consumed_tokens = {execution_context: ec_consumed_tokens}
        # Remove values on edges
        execution_context.incoming_edge_tokens[node] = {
            edge: [
                v
                for v in execution_context.incoming_edge_tokens[node][edge]
                if v not in consumed_tokens[execution_context]
            ]
            for edge in execution_context.incoming_edge_tokens[node]
        }
        return consumed_tokens

    def executable_activity_nodes(
        self, execution_context, tokens_added
    ) -> List[ActivityNode]:
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
            execution_context.incoming_edge_tokens[target][t.get_edge()].append(t)
            execution_context.candidate_clusters[
                target.identity
            ] = execution_context.candidate_clusters.get(target.identity, []) + [t]
            updated_clusters.add(target)

        enabled_nodes = [
            n
            for n in updated_clusters
            if n.enabled(
                execution_context.incoming_edge_tokens[n],
                permissive=self.permissive,
            )
        ]
        enabled_nodes.sort(
            key=lambda x: x.identity
        )  # Avoid any ordering non-determinism

        return enabled_nodes

    def post_process(
        self,
        execution_context: ExecutionContext,
        record: ActivityNodeExecution,
        new_tokens: List[ActivityEdgeFlow],
    ):
        node = record.get_node()
        if isinstance(node, ActivityParameterNode) and node.get_parameter().is_output():
            execution_context.parameter_values += [
                ParameterValue(
                    parameter=node.get_parameter(),
                    value=literal(node.value(), reference=True),
                )
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
