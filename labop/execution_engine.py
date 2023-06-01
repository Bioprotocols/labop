import datetime
import hashlib
import logging
import os
import uuid
from abc import ABC
from typing import Callable, Dict, List, Union
from urllib.parse import quote, unquote

import graphviz
import pandas as pd
import sbol3
import xarray as xr
from numpy import record

import labop
import uml
from labop_convert.behavior_dynamics import SampleProvenanceObserver

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

UUID_SEED = "LabOP"
m = hashlib.md5()


def new_uuid():
    m.update(UUID_SEED.encode("utf-8"))
    return uuid.UUID(m.hexdigest())


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
        specializations: List["BehaviorSpecialization"] = [],
        use_ordinal_time=False,
        failsafe=True,
        permissive=False,
        use_defined_primitives=True,
        sample_format="xarray",
        out_dir="out",
        dataset_file=None,
        track_samples=True,
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
        self.track_samples = track_samples

        self.prov_observer = (
            SampleProvenanceObserver(self.out_dir) if self.track_samples else None
        )

        if self.specializations is None or (
            isinstance(self.specializations, list) and len(self.specializations) == 0
        ):
            from labop_convert import DefaultBehaviorSpecialization

            self.specializations = [DefaultBehaviorSpecialization()]

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
        protocol: labop.Protocol,
        agent: sbol3.Agent,
        id: str = new_uuid(),
        parameter_values: List[labop.ParameterValue] = {},
    ):
        # Record in the document containing the protocol
        doc = protocol.document

        # setup possible issues
        self.issues[id] = []

        if self.use_defined_primitives:
            from labop.primitive_execution import initialize_primitive_compute_output

            # Define the compute_output function for known primitives
            initialize_primitive_compute_output(doc)

        # First, set up the record for the protocol and parameter values
        self.ex = labop.ProtocolExecution(id, protocol=protocol)
        doc.add(self.ex)

        self.ex.association.append(sbol3.Association(agent=agent, plan=protocol))
        self.ex.parameter_values = parameter_values

        # Initialize specializations
        for specialization in self.specializations:
            specialization.initialize_protocol(self.ex, out_dir=self.out_dir)
            specialization.on_begin(self.ex)

    def finalize(
        self,
        protocol: labop.Protocol,
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
        protocol: labop.Protocol,
        agent: sbol3.Agent,
        parameter_values: List[labop.ParameterValue] = {},
        id: str = new_uuid(),
        start_time: datetime.datetime = None,
    ) -> labop.ProtocolExecution:
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

    def run(self, protocol: labop.Protocol, start_time: datetime.datetime = None):
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
        ready: List[uml.ActivityNode],
        node_outputs: Dict[uml.ActivityNode, Callable] = {},
    ):
        non_call_nodes = [
            node for node in ready if not isinstance(node, uml.CallBehaviorAction)
        ]
        new_tokens = []
        # prefer executing non_call_nodes first
        for node in non_call_nodes + [n for n in ready if n not in non_call_nodes]:
            self.current_node = node
            try:
                tokens_added, tokens_removed = node.execute(
                    self,
                    node_outputs=(node_outputs[node] if node in node_outputs else None),
                )
                self.tokens = [t for t in self.tokens if t not in tokens_removed]

                new_tokens = new_tokens + tokens_added
                self.tokens = self.tokens + tokens_added
                record = self.ex.executions[-1]
                self.post_process(record, new_tokens)

            except Exception as e:
                # Consume the tokens used by the node that caused the exception
                # Produce control tokens
                # incoming_flows = [
                #     t for t in self.tokens if node == t.get_target()
                # ]
                # exec = labop.CallBehaviorExecution(
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
                #     and (isinstance(edge, uml.ControlFlow))
                # ]

                # self.tokens = [
                #     t for t in self.tokens if t.get_target() != node
                # ] + [
                #     labop.ActivityEdgeFlow(
                #         token_source=exec,
                #         edge=edge,
                #         value=uml.literal("uml.ControlFlow"),
                #     )
                #     for edge in control_edges
                # ]
                if self.permissive:
                    self.issues[self.ex.display_id].append(ExecutionWarning(e))
                else:
                    self.issues[self.ex.display_id].append(ExecutionError(e))
                    raise (e)
        # self.tokens = self.tokens + new_tokens
        return self.executable_activity_nodes(new_tokens)

    def executable_activity_nodes(self, tokens_added) -> List[uml.ActivityNode]:
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
            self.candidate_clusters[target.identity] = self.candidate_clusters.get(
                target.identity, []
            ) + [t]
            updated_clusters.add(target)

        enabled_nodes = [
            n
            for n in updated_clusters
            if n.enabled(self, self.candidate_clusters[n.identity])
        ]

        # clear candidate clusters for enabled nodes
        for n in enabled_nodes:
            self.candidate_clusters[n.identity] = []

        enabled_nodes.sort(
            key=lambda x: x.identity
        )  # Avoid any ordering non-determinism

        return enabled_nodes

    def post_process(
        self,
        record: labop.ActivityNodeExecution,
        new_tokens: List[labop.ActivityEdgeFlow],
    ):
        if self.dataset_file is not None:
            self.write_data_templates(record, new_tokens)

        if self.track_samples and isinstance(
            record.node.lookup(), uml.CallBehaviorAction
        ):
            self.prov_observer.update(record)

    def write_data_templates(
        self,
        record: labop.ActivityNodeExecution,
        new_tokens: List[labop.ActivityEdgeFlow],
    ):
        """
        Write a data template as an xlsx file if the record.node produces sample data (i.e., it has an output of type labop.Dataset with a data attribute of type labop.SampleData)
        Parameters
        ----------
        node : labop.ActivityNodeExecution
            ActivityNodeExecution that produces SampleData
        """
        if not isinstance(record, labop.CallBehaviorExecution):
            return

        # Find all labop.Dataset objects produced by record
        datasets = [
            token.value.get_value()
            for token in new_tokens
            if token.token_source == record.identity
            and isinstance(token.value.get_value(), labop.Dataset)
        ]
        sample_data = [
            dataset.data
            for dataset in datasets
            if isinstance(dataset.data, labop.SampleData)
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
    def run(self, protocol: labop.Protocol, start_time: datetime.datetime = None):
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

    def advance(self, ready: List[uml.ActivityNode]):
        def auto_advance(r):
            # If Node is a CallBehavior action, then:
            if isinstance(r, uml.CallBehaviorAction):
                behavior = r.behavior.lookup()
                return (  # It is a subprotocol
                    isinstance(behavior, labop.Protocol)
                    or (len(list(behavior.get_outputs())) == 0)  # Has no output pins
                    or (  # Overrides the (empty) default implementation of compute_output()
                        not hasattr(behavior.compute_output, "__func__")
                        or behavior.compute_output.__func__
                        != labop.primitive_execution.primitive_compute_output
                    )
                )
            else:
                return True

        auto_advance_nodes = [r for r in ready if auto_advance(r)]

        while len(auto_advance_nodes) > 0:
            ready = self.step(auto_advance_nodes)
            auto_advance_nodes = [r for r in ready if auto_advance(r)]

        return self.executable_activity_nodes()

    def ready_message(self, ready: List[uml.ActivityNode]):
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
            if isinstance(r, uml.CallBehaviorAction)
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

    def next(self, activity_node: uml.ActivityNode, node_output: callable):
        """Execute a single ActivityNode using the node_output function to calculate its output pin values.

        Args:
            activity_node (uml.ActivityNode): node to execute
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


def sum_measures(measure_list):
    """Add a list of measures and return a fresh measure
    Note: requires that all have the same unit and types

    Parameters
    ----------
    measure_list of SBOL Measure objects

    Returns
    -------
    New Measure object with the sum of input measure amounts
    """
    prototype = measure_list[0]
    if not all(
        m.types == prototype.types and m.unit == prototype.unit for m in measure_list
    ):
        raise ValueError(
            f"Can only merge measures with identical units and types: {([m.value, m.unit, m.types] for m in measure_list)}"
        )
    total = sum(m.value for m in measure_list)
    return sbol3.Measure(value=total, unit=prototype.unit, types=prototype.types)


def protocol_execution_aggregate_child_materials(self):
    """Merge the consumed material from children, adding a fresh Material for each to this record.

    Parameters
    ----------
    self: ProtocolExecution object
    """
    child_materials = [
        e.call.consumed_material
        for e in self.executions
        if isinstance(e, labop.CallBehaviorExecution)
        and hasattr(e.call, "consumed_material")
    ]
    specifications = {m.specification for m in child_materials}
    self.consumed_material = (
        labop.Material(
            s,
            sum_measures([m.amount for m in child_materials if m.specification == s]),
        )
        for s in specifications
    )


labop.ProtocolExecution.aggregate_child_materials = (
    protocol_execution_aggregate_child_materials
)


def protocol_execution_to_dot(
    self,
    execution_engine=None,
    ready: List[uml.ActivityNode] = [],
    done=set([]),
    out_dir="out",
):
    """
    Create a dot graph that illustrates edge values appearing the execution of the protocol.
    :param self:
    :return: graphviz.Digraph
    """
    dot = graphviz.Digraph(
        comment=self.protocol,
        strict=True,
        graph_attr={"rankdir": "TB", "concentrate": "true"},
        node_attr={"ordering": "out"},
    )

    def _make_object_edge(dot, incoming_flow, target, dest_parameter=None):
        flow_source = incoming_flow.lookup().token_source.lookup()
        source = incoming_flow.lookup().edge.lookup().source.lookup()
        value = incoming_flow.lookup().value.get_value()
        is_ref = isinstance(incoming_flow.lookup().value, uml.LiteralReference)
        # value = value.value.lookup() if isinstance(value, uml.LiteralReference) else value.value

        if isinstance(source, uml.Pin):
            src_parameter = (
                source.get_parent().pin_parameter(source.name).property_value
            )
            src_var = src_parameter.name
        else:
            src_var = ""

        dest_var = dest_parameter.name if dest_parameter else ""

        source_id = source.dot_label(parent_identity=self.protocol)
        if isinstance(source, uml.CallBehaviorAction):
            source_id = f"{source_id}:node"
        target_id = target.dot_label(parent_identity=self.protocol)
        if isinstance(target, uml.CallBehaviorAction):
            target_id = f"{target_id}:node"

        if isinstance(value, sbol3.Identified):
            edge_label = value.display_id  # value.identity
        else:
            edge_label = f"{value}"

        if False and hasattr(value, "to_dot") and not is_ref:
            # Make node for value and connect to source
            value_node_id = value.to_dot(dot, out_dir=out_dir)
            dot.edge(source_id, value_node_id)

        edge_index = incoming_flow.split("ActivityEdgeFlow")[-1]

        edge_label = f"{edge_index}: {edge_label}"

        attrs = {"color": "orange"}
        dot.edge(target_id, source_id, edge_label, _attributes=attrs)

    dot = graphviz.Digraph(
        name=f"cluster_{self.identity}", graph_attr={"label": self.identity}
    )

    # Protocol graph
    protocol_graph = self.protocol.lookup().to_dot(ready=ready, done=done)
    dot.subgraph(protocol_graph)

    if execution_engine and execution_engine.current_node:
        current_node_id = execution_engine.current_node.dot_label(
            parent_identity=self.protocol
        )
        current_node_id = f"{current_node_id}:node"
        dot.edge(
            current_node_id,
            current_node_id,
            _attributes={
                "tailport": "w",
                "headport": "w",
                "taillabel": "current_node",
                "color": "red",
            },
        )

    # Execution graph
    for execution in self.executions:
        exec_target = execution.node.lookup()
        execution_label = ""

        # Make a self loop that includes the and start and end time.
        if isinstance(execution, labop.CallBehaviorExecution):
            time_format = "%H:%M:%S"
            start_time = datetime.datetime.strftime(
                execution.call.lookup().start_time, time_format
            )
            end_time = datetime.datetime.strftime(
                execution.call.lookup().end_time, time_format
            )
            if start_time == end_time:
                execution_label += f"[{start_time}]"
            else:
                execution_label += f"[{start_time},\n  {end_time}]"
            target_id = exec_target.dot_label(parent_identity=self.protocol)
            target_id = f"{target_id}:node"
            dot.edge(
                target_id,
                target_id,
                _attributes={
                    "tailport": "w",
                    "headport": "w",
                    "taillabel": execution_label,
                    "color": "invis",
                },
            )

        for incoming_flow in execution.incoming_flows:
            # Executable Nodes have incoming flow from their input pins and ControlFlows
            flow_source = incoming_flow.lookup().token_source.lookup()
            exec_source = flow_source.node.lookup()
            edge_ref = incoming_flow.lookup().edge
            if edge_ref and isinstance(edge_ref.lookup(), uml.ObjectFlow):
                if isinstance(exec_target, uml.ActivityParameterNode):
                    # ActivityParameterNodes are ObjectNodes that have a parameter
                    _make_object_edge(
                        dot,
                        incoming_flow,
                        exec_target,
                        dest_parameter=exec_target.parameter.lookup(),
                    )
                elif isinstance(exec_target, uml.ControlNode):
                    # This in an object flow into the node itself, which happens for ControlNodes
                    _make_object_edge(dot, incoming_flow, exec_target)
            elif isinstance(exec_source, uml.Pin):
                # This incoming_flow is from an input pin, and need the flow into the pin
                for into_pin_flow in flow_source.incoming_flows:
                    # source = src_to_pin_edge.source.lookup()
                    # target = src_to_pin_edge.target.lookup()
                    dest_parameter = exec_target.pin_parameter(
                        exec_source.name
                    ).property_value
                    _make_object_edge(
                        dot,
                        into_pin_flow,
                        into_pin_flow.lookup().edge.lookup().target.lookup(),
                        dest_parameter=dest_parameter,
                    )
            elif (
                isinstance(exec_source, uml.DecisionNode)
                and edge_ref
                and isinstance(edge_ref.lookup(), uml.ControlFlow)
            ):
                _make_object_edge(dot, incoming_flow, exec_target)

    return dot


labop.ProtocolExecution.to_dot = protocol_execution_to_dot
