from abc import ABC, abstractmethod
import uuid
import datetime
import itertools

import paml
import sbol3


class ExecutionEngine(ABC):
    """Base class for implementing and recording a PAML executions.
    This class can handle common UML activities and the propagation of tokens, but does not execute primitives.
    It needs to be extended with specific implementations that have that capability.
    """

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
        ex = paml.ProtocolExecution(id)
        doc.add(ex)
        ex.start_time = str(datetime.datetime.now()) # TODO: remove str wrapper after sbol_factory #22 fixed
        ex.associations.append(sbol3.Association(agent=agent, plan=protocol))
        ex.parameter_values = \
            [paml.ParameterValue(parameter=p, value=literal(p,reference=True)) for p, v in parameter_values.items()]

        # Iteratively execute all unblocked activities until no more tokens can progress
        tokens = []  # no tokens to start
        ready = protocol.initiating_nodes()
        while ready:
            for node in ready:
                tokens = execute_activity_node(ex, node, tokens)
            ready = executable_activity_nodes(protocol, tokens)

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
            candidate_clusters[t.edge.target] = candidate_clusters.get(t.edge.target,[])+[t]
        return [n for n,nt in candidate_clusters if {t.edge for t in nt}==p.incoming_edges(n)]

    def execute_activity_node(self, ex: paml.ProtocolExecution, node: uml.ActivityNode,
                              tokens: list[paml.ActivityEdgeFlow]) -> list[paml.ActivityEdgeFlow]:
        """Execute an node in an activity, consuming the incoming flows and recording execution and outgoing flows

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
        inputs = [t for t in tokens if t.edge.target == node.identity] # TODO change to pointer lookup after pySBOL #237
        # Create a record for the node execution
        record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
        ex.executions.append(record)
        # Dispatch execution based on node type, collecting any object flows produced
        # The dispatch methods are the ones that can (or must be) overridden for a particular execution environment
        if isinstance(node, uml.InitialNode):
            if len(inputs) != 0:
                raise ValueError(f'Initial node must have zero inputs, but {node.identity} had {len(inputs)}')
            execute_initialnode(node)
            # put a control token on all outgoing edges

        elif isinstance(node, uml.FlowFinalNode):
            execute_finalnode(node, inputs)

        elif isinstance(node, uml.ForkNode):
            if len(inputs) != 1:
                raise ValueError(f'Fork node must have precisely one input, but {node.identity} had {len(inputs)}')
            record, tokens = execute_forknode(node,inputs[0])
            pass

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
            if
                record.call = execute()
            pass
        else:
            raise ValueError(f'Do not know how to execute node {node.identity} of type {node.type_uri}')

        # Send outgoing control flows
        # Check that outgoing flows don't conflict with
        # return updated token list
        return [t for t in tokens if t not in inputs] + new_tokens

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
    child_materials = [e.call.consumed_material for e in ex.executions if isinstance(e, CallBehaviorExecution)]
    specifications = {m.specification for m in child_materials}
    self.consumed_material = (paml.Material(s,sum_measures([m.amount for m in child_materials if m.specification==s]))
                              for s in specifications)
ProtocolExecution.aggregate_child_materials = protocol_execution_aggregate_child_materials
