from abc import ABC, abstractmethod
import uuid
import datetime
import itertools

import paml
import uml
import sbol3


class ExecutionEngine(ABC):
    """Base class for implementing and recording a PAML executions.
    This class can handle common UML activities and the propagation of tokens, but does not execute primitives.
    It needs to be extended with specific implementations that have that capability.
    """

    def __init__(self):
        self.node_counters = {}

    def next_id(self, node : uml.InvocationAction):
        self.node_counters[node.identity] = self.node_counters.get(node.identity, 0)
        next = self.node_counters[node.identity]
        self.node_counters[node.identity] += 1
        return next

    def execute(self, protocol: paml.Protocol, agent: sbol3.Agent, parameter_values: dict = {}, id: str = uuid.uuid4()) -> paml.ProtocolExecution:
        """Execute the given protocol against the provided parameters

        Parameters
        ----------
        protocol: Protocol to execute
        agent: Agent that is executing this protocol
        parameter_values: Dictionary containing all input parameter values (if any)
        id: display_id or URI to be used as the name of this execution; defaults to a UUID display_id

        Returns
        -------
        ProtocolExecution containing a record of the execution
        """

        # Record in the document containing the protocol
        doc = protocol.document

        # First, set up the record for the protocol and parameter values
        ex = paml.ProtocolExecution(id, protocol=protocol)
        doc.add(ex)
        ex.start_time = str(datetime.datetime.now()) # TODO: remove str wrapper after sbol_factory #22 fixed
        ex.association.append(sbol3.Association(agent=agent, plan=protocol))
        ex.parameter_values = \
            [paml.ParameterValue(parameter=p, value=literal(p,reference=True)) for p, v in parameter_values.items()]

        # Iteratively execute all unblocked activities until no more tokens can progress
        tokens = []  # no tokens to start
        ready = protocol.initiating_nodes()
        while ready:
            for node in ready:
                tokens = self.execute_activity_node(ex, node, tokens)
            ready = self.executable_activity_nodes(protocol, tokens)

        # TODO: finish implementing
        # TODO: ensure that only one token is allowed per edge
        # TODO: think about infinite loops and how to abort

        # A Protocol has completed normally if all of its required output parameters have values
        set_parameters = (p.parameter for p in ex.parameter_values)
        ex.completed_normally = all(p in set_parameters for p in protocol.get_required_outputs())

        # aggregate consumed material records from all behaviors executed within, mark end time, and return
        ex.aggregate_child_materials()
        ex.end_time = str(datetime.datetime.now()) # TODO: remove str wrapper after sbol_factory #22 fixed
        return ex

    def executable_activity_nodes(self, protocol: paml.Protocol, tokens: list[paml.ActivityEdgeFlow])\
            -> list[uml.ActivityNode]:
        """Find all of the activity nodes that are ready to be run given the current set of tokens
        Note that this will NOT identify activities with no in-flows: those are only set up as initiating nodes

        Parameters
        ----------
        protocol: paml.Protocol being executed
        tokens: set of ActivityEdgeFlow records that have not yet been consumed

        Returns
        -------
        List of ActivityNodes that are ready to be run
        """
        candidate_clusters = {}
        for t in tokens:
            target = protocol.document.find(protocol.document.find(t.edge).target)
            candidate_clusters[target] = candidate_clusters.get(target,[])+[t]
        return [n for n,nt in candidate_clusters.items()
                  if {protocol.document.find(t.edge) for t in nt}==protocol.incoming_edges(n)]

    def execute_activity_node(self, ex : paml.ProtocolExecution, node: uml.ActivityNode,
                              tokens: list[paml.ActivityEdgeFlow]) -> list[paml.ActivityEdgeFlow]:
        """Execute a node in an activity, consuming the incoming flows and recording execution and outgoing flows

        Parameters
        ----------
        ex: Current execution record
        node: node to be executed
        tokens: current list of pending edge flows

        Returns
        -------
        updated list of pending edge flows
        """
        # Extract the relevant set of incoming flow values
        inputs = [t for t in tokens
                    if ex.document.find(t.edge).target == node.identity] # TODO change to pointer lookup after pySBOL #237
        # Create a record for the node execution
        record = None
        new_tokens = []

        # Dispatch execution based on node type, collecting any object flows produced
        # The dispatch methods are the ones that can (or must be) overridden for a particular execution environment
        if isinstance(node, uml.InitialNode):
            if len(inputs) != 0:
                raise ValueError(f'Initial node must have zero inputs, but {node.identity} had {len(inputs)}')
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            new_tokens = self.next_tokens(record, ex)
            # put a control token on all outgoing edges

        elif isinstance(node, uml.FlowFinalNode):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            new_tokens = self.next_tokens(record, ex)

        elif isinstance(node, uml.ForkNode):
            if len(inputs) != 1:
                raise ValueError(f'Fork node must have precisely one input, but {node.identity} had {len(inputs)}')
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            new_tokens = self.next_tokens(record, ex)

        # elif isinstance(node, uml.JoinNode):
        #     pass
        # elif isinstance(node, uml.MergeNode):
        #     pass
        # elif isinstance(node, uml.DecisionNode):
        #     pass
        elif isinstance(node, uml.ActivityParameterNode):
            pass
        elif isinstance(node, uml.CallBehaviorAction):
            record = paml.CallBehaviorExecution(node=node, incoming_flows=inputs)
            call = paml.BehaviorExecution(f"execute_{node.identity}_{self.next_id(node)}",
                                            parameter_values=[paml.ParameterValue(parameter=param,
                                                                                  value=pin.value
                                                                                  if hasattr(pin, "value") else None)
                                                              for pin in node.inputs
                                                              for param in ex.document.find(node.behavior).parameters
                                                              if pin.name == param.name],
                                            completed_normally=True,
                                            consumed_material=[]) # FIXME handle materials
            record.call = call
            ex.document.add(call)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.Pin):
            pass
        else:
            raise ValueError(f'Do not know how to execute node {node.identity} of type {node.type_uri}')

        if record: # Pins will not generate records
            ex.executions.append(record)

        # Send outgoing control flows
        # Check that outgoing flows don't conflict with
        # return updated token list
        return [t for t in tokens if t not in inputs] + new_tokens

    def next_tokens(self, activity_node: paml.ActivityNodeExecution, ex: paml.ProtocolExecution):
        protocol = ex.document.find(ex.protocol)
        tokens = [paml.ActivityEdgeFlow(edge=edge, token_source=activity_node)
                  for edge in protocol.edges
                  if activity_node.node in edge.source]
        return tokens


    def execute_primitive(self, behavior: paml.Primitive, agent: sbol3.Agent, parameter_values: dict = {}, id: str = uuid.uuid4()) -> paml.BehaviorExecution:
        pass


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

