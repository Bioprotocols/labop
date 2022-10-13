from abc import ABC, abstractmethod
import re
from typing import Callable, Dict, List
import uuid
import datetime
import logging

import pandas as pd
import graphviz
import sbol3

import paml
import uml
import sbol3


from paml_convert.behavior_specialization import BehaviorSpecialization, DefaultBehaviorSpecialization
from paml.primitive_execution import initialize_primitive_compute_output


l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


failsafe = True  # When set to True, a protocol execution will proceed through to the end, even if a CallBehaviorAction raises an exception.  Set to False for debugging


class ExecutionEngine(ABC):
    """Base class for implementing and recording a PAML executions.
    This class can handle common UML activities and the propagation of tokens, but does not execute primitives.
    It needs to be extended with specific implementations that have that capability.
    """

    def __init__(self,
                 specializations: List[BehaviorSpecialization] = [DefaultBehaviorSpecialization()],
                 use_ordinal_time = False, failsafe=True, permissive=False):
        self.exec_counter = 0
        self.variable_counter = 0
        self.specializations = specializations

        # The EE uses a configurable start_time as the reference time.
        # Because the start_time is not always the actual time, then
        # we need to set times relative to the start time using the
        # relative wall clock time.
        # if use_oridinal_time, then use a new int for each time
        self.start_time = None  # The official start_time
        self.wall_clock_start_time = None # The actual now() time
        self.use_ordinal_time = use_ordinal_time # Use int instead of datetime
        self.ordinal_time = None
        self.current_node = None
        self.blocked_nodes = set({})
        self.tokens = []  # no tokens to start
        self.ex = None
        self.is_asynchronous = True
        self.failsafe = failsafe
        self.permissive = permissive # Allow execution to follow control flow even if objects not present.


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
            self.ordinal_time = datetime.datetime.strptime("1/1/00 00:00:00", "%d/%m/%y %H:%M:%S")
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
        rel_start =  now - start
        cur_time = self.start_time + rel_start
        return  cur_time if not as_string else str(cur_time)


    def initialize(
        self,
        protocol: paml.Protocol,
        agent: sbol3.Agent,
        id: str = uuid.uuid4(),
        parameter_values: List[paml.ParameterValue] = {},
    ):
        # Record in the document containing the protocol
        doc = protocol.document

        # Define the compute_output function for known primitives
        initialize_primitive_compute_output(doc)

        # First, set up the record for the protocol and parameter values
        self.ex = paml.ProtocolExecution(id, protocol=protocol)
        doc.add(self.ex)

        self.ex.association.append(sbol3.Association(agent=agent, plan=protocol))
        self.ex.parameter_values = parameter_values

        # Initialize specializations
        for specialization in self.specializations:
            specialization.initialize_protocol(self.ex)
            specialization.on_begin(self.ex)

    def finalize(
        self,
        protocol: paml.Protocol,
    ):
        self.ex.end_time = self.get_current_time()

        # A Protocol has completed normally if all of its required output parameters have values
        self.ex.completed_normally = set(protocol.get_required_inputs()).issubset(set([p.parameter.lookup() for p in self.ex.parameter_values]))

        # aggregate consumed material records from all behaviors executed within, mark end time, and return
        self.ex.aggregate_child_materials()


        # End specializations
        for specialization in self.specializations:
            specialization.on_end(self.ex)

    def execute(self,
                protocol: paml.Protocol,
                agent: sbol3.Agent,
                parameter_values: List[paml.ParameterValue] = {},
                id: str = uuid.uuid4(),
                start_time: datetime.datetime = None
                ) -> paml.ProtocolExecution:
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

    def run(
        self,
        protocol: paml.Protocol,
        start_time: datetime.datetime = None
    ):

        self.init_time(start_time)
        self.ex.start_time = self.start_time # TODO: remove str wrapper after sbol_factory #22 fixed

        ready = protocol.initiating_nodes()

        # Iteratively execute all unblocked activities until no more tokens can progress
        while ready:
            non_call_nodes = [node for node in ready if not isinstance(node, uml.CallBehaviorAction)]
            if non_call_nodes:
                ready = self.step(non_call_nodes)
            else:
                ready = self.step(ready)
        return ready


    def step(
        self,
        ready: List[uml.ActivityNode],
        node_outputs: Dict[uml.ActivityNode, Callable] = {}
    ):
        for node in ready:
            self.current_node = node
            self.tokens = node.execute(
                self,
                node_outputs=(node_outputs[node]
                              if node in node_outputs
                              else None))
        return self.executable_activity_nodes()

    def executable_activity_nodes(
        self
    ) -> List[uml.ActivityNode]:
        """Find all of the activity nodes that are ready to be run given the current set of tokens
        Note that this will NOT identify activities with no in-flows: those are only set up as initiating nodes

        Parameters
        ----------

        Returns
        -------
        List of ActivityNodes that are ready to be run
        """
        candidate_clusters = {}
        for t in self.tokens:
            target = t.get_target()
            candidate_clusters[target] = candidate_clusters.get(target,[])+[t]
        return [n for n,nt in candidate_clusters.items()
                if n.enabled(self, nt)]





class ManualExecutionEngine(ExecutionEngine):
    def run(
        self,
        protocol: paml.Protocol,
        start_time: datetime.datetime = None
    ):
        self.init_time(start_time)
        self.ex.start_time = self.start_time # TODO: remove str wrapper after sbol_factory #22 fixed
        ready = protocol.initiating_nodes()
        ready = self.advance(ready)
        choices = self.ready_message(ready)
        graph = self.ex.to_dot(ready=ready, done=self.ex.backtrace()[0])
        return ready, choices, graph

    def advance(
        self,
        ready: List[uml.ActivityNode]
    ):
        def auto_advance(r):
            # If Node is a CallBehavior action, then:
            if isinstance(r, uml.CallBehaviorAction):
                behavior = r.behavior.lookup()
                return ( \
                    # It is a subprotocol
                    isinstance(behavior, paml.Protocol) or \
                    # Has no output pins
                    (len(list(behavior.get_outputs())) == 0) or \
                    # Overrides the (empty) default implementation of compute_output()
                    (not hasattr(behavior.compute_output, "__func__") or
                        behavior.compute_output.__func__ != paml.primitive_execution.primitive_compute_output)
                )
            else:
                return True

        auto_advance_nodes = [r for r in ready if auto_advance(r)]

        while len(auto_advance_nodes) > 0:
            ready = self.step(auto_advance_nodes)
            auto_advance_nodes = [r for r in ready if auto_advance(r)]

        return self.executable_activity_nodes()


    def ready_message(
        self,
        ready: List[uml.ActivityNode]
    ):
        msg = "Activities Ready to Execute:\n"

        def activity_name(a):
            return a.display_id
        def behavior_name(a):
            return a.display_id
        def decision_name(a):
            return a.identity

        activities = [activity_name(r.protocol()) for r in ready]
        behaviors = [behavior_name(r.behavior.lookup()) if isinstance(r, uml.CallBehaviorAction) else decision_name(r) for r in ready]
        identities = [r.identity for r in ready]
        choices = pd.DataFrame({ "Activity": activities, "Behavior": behaviors, "Identity": identities })
        #ready_nodes = "\n".join([f"{idx}: {r.behavior}" for idx, r in enumerate(ready)])
        return display(HTML("<div style='height: 200px; overflow: auto; width: fit-content'>" +
             choices.to_html() +
             "</div>"))
        #return choices #f"{msg}{ready_nodes}"

    def next(
        self,
        activity_node: uml.ActivityNode,
        node_output: callable
    ):
        """Execute a single ActivityNode using the node_output function to calculate its output pin values.

        Args:
            activity_node (uml.ActivityNode): node to execute
            node_output (callable): function to calculate output pins

        Returns:
            _type_: _description_
        """
        successors = self.step([activity_node], node_outputs={activity_node: node_output})
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
    if not all(m.types == prototype.types and m.unit == prototype.unit for m in measure_list):
        raise ValueError(f'Can only merge measures with identical units and types: {([m.value, m.unit, m.types] for m in measure_list)}')
    total = sum(m.value for m in measure_list)
    return sbol3.Measure(value=total, unit=prototype.unit, types=prototype.types)


def protocol_execution_aggregate_child_materials(self):
    """Merge the consumed material from children, adding a fresh Material for each to this record.

    Parameters
    ----------
    self: ProtocolExecution object
    """
    child_materials = [e.call.consumed_material for e in self.executions
                       if isinstance(e, paml.CallBehaviorExecution) and
                          hasattr(e.call, "consumed_material")]
    specifications = {m.specification for m in child_materials}
    self.consumed_material = (paml.Material(s,sum_measures([m.amount for m in child_materials if m.specification==s]))
                              for s in specifications)
paml.ProtocolExecution.aggregate_child_materials = protocol_execution_aggregate_child_materials


def protocol_execution_to_dot(self, execution_engine=None, ready: List[uml.ActivityNode] = [], done=set([])):
    """
    Create a dot graph that illustrates edge values appearing the execution of the protocol.
    :param self:
    :return: graphviz.Digraph
    """
    dot = graphviz.Digraph(comment=self.protocol,
                           strict=True,
                           graph_attr={"rankdir": "TB",
                                       "concentrate": "true"},
                           node_attr={"ordering": "out"})
    def _make_object_edge(dot, incoming_flow, target, dest_parameter=None):
        flow_source = incoming_flow.lookup().token_source.lookup()
        source = incoming_flow.lookup().edge.lookup().source.lookup()
        value = incoming_flow.lookup().value.get_value()
        #value = value.value.lookup() if isinstance(value, uml.LiteralReference) else value.value

        if isinstance(source, uml.Pin):
            src_parameter = source.get_parent().pin_parameter(source.name).property_value
            src_var = src_parameter.name
        else:
            src_var = ""

        dest_var = dest_parameter.name if dest_parameter else ""

        source_id = source.dot_label(parent_identity=self.protocol)
        if isinstance(source, uml.CallBehaviorAction):
            source_id = f'{source_id}:node'
        target_id = target.dot_label(parent_identity=self.protocol)
        if isinstance(target, uml.CallBehaviorAction):
            target_id = f'{target_id}:node'

        if isinstance(value, sbol3.Identified):
            edge_label = value.identity
        else:
            edge_label = f"{value}"

        edge_index = incoming_flow.split("ActivityEdgeFlow")[-1]

        edge_label = f"{edge_index}: {edge_label}"

        attrs = {"color": "orange"}
        dot.edge(source_id, target_id, edge_label, _attributes=attrs)


    dot = graphviz.Digraph(name=f"cluster_{self.identity}",
                           graph_attr={
                               "label": self.identity
                           })

    # Protocol graph
    protocol_graph = self.protocol.lookup().to_dot(ready=ready, done=done)
    dot.subgraph(protocol_graph)

    if execution_engine and execution_engine.current_node:
        current_node_id = execution_engine.current_node.dot_label(parent_identity=self.protocol)
        current_node_id = f'{current_node_id}:node'
        dot.edge(current_node_id, current_node_id,  _attributes={"tailport": "w",
                                                         "headport": "w",
                                                         "taillabel": "current_node",
                                                         "color": "red"})

    # Execution graph
    for execution in self.executions:
        exec_target = execution.node.lookup()
        execution_label = ""

        # Make a self loop that includes the and start and end time.
        if isinstance(execution, paml.CallBehaviorExecution):
            execution_label += f"[{execution.call.lookup().start_time},\n  {execution.call.lookup().end_time}]"
            target_id = exec_target.dot_label(parent_identity=self.protocol)
            target_id = f'{target_id}:node'
            dot.edge(target_id, target_id,  _attributes={"tailport": "w",
                                                         "headport": "w",
                                                         "taillabel": execution_label,
                                                         "color": "invis"})

        for incoming_flow in execution.incoming_flows:
            # Executable Nodes have incoming flow from their input pins and ControlFlows
            flow_source = incoming_flow.lookup().token_source.lookup()
            exec_source = flow_source.node.lookup()
            edge_ref = incoming_flow.lookup().edge
            if edge_ref and isinstance(edge_ref.lookup(), uml.ObjectFlow):
                if isinstance(exec_target, uml.ActivityParameterNode):
                    # ActivityParameterNodes are ObjectNodes that have a parameter
                    _make_object_edge(dot, incoming_flow, exec_target, dest_parameter=exec_target.parameter.lookup())
                elif isinstance(exec_target, uml.ControlNode):
                    # This in an object flow into the node itself, which happens for ControlNodes
                    _make_object_edge(dot, incoming_flow, exec_target)
            elif isinstance(exec_source, uml.Pin):
                # This incoming_flow is from an input pin, and need the flow into the pin
                into_pin_flow = flow_source.incoming_flows[0]
                #source = src_to_pin_edge.source.lookup()
                #target = src_to_pin_edge.target.lookup()
                dest_parameter = exec_target.pin_parameter(exec_source.name).property_value
                _make_object_edge(dot, into_pin_flow, into_pin_flow.lookup().edge.lookup().target.lookup(), dest_parameter=dest_parameter)
            elif isinstance(exec_source, uml.DecisionNode) and edge_ref and isinstance(edge_ref.lookup(), uml.ControlFlow):
                _make_object_edge(dot, incoming_flow, exec_target)

    return dot
paml.ProtocolExecution.to_dot = protocol_execution_to_dot
