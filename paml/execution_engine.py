from abc import ABC, abstractmethod
import re
from typing import List
import uuid
import datetime
import logging
import sys

import pandas as pd
import graphviz
import sbol3

import paml
import uml
from paml_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, num2row
from paml_convert.behavior_specialization import BehaviorSpecialization, DefaultBehaviorSpecialization



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
                 use_ordinal_time = False):
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

        Returns
        -------
        ProtocolExecution containing a record of the execution
        """

        # Record in the document containing the protocol
        doc = protocol.document

        # First, set up the record for the protocol and parameter values
        ex = paml.ProtocolExecution(id, protocol=protocol)
        doc.add(ex)

        ex.association.append(sbol3.Association(agent=agent, plan=protocol))
        ex.parameter_values = parameter_values

        # Initialize specializations
        for specialization in self.specializations:
            specialization.initialize_protocol(ex)
            specialization.on_begin(ex)

        self.init_time(start_time)
        ex.start_time = self.start_time # TODO: remove str wrapper after sbol_factory #22 fixed

        # Iteratively execute all unblocked activities until no more tokens can progress
        tokens = []  # no tokens to start
        ready = protocol.initiating_nodes()
        while ready:
            for node in ready:
                self.current_node = node
                tokens = self.execute_activity_node(ex, node, tokens)
            ready = self.executable_activity_nodes(ex, tokens)

        ex.end_time = self.get_current_time()

        # TODO: finish implementing
        # TODO: ensure that only one token is allowed per edge
        # TODO: think about infinite loops and how to abort

        # A Protocol has completed normally if all of its required output parameters have values
        set_parameters = (p.parameter.lookup() for p in ex.parameter_values)
        ex.completed_normally = all(p in set_parameters for p in protocol.get_required_outputs())

        # aggregate consumed material records from all behaviors executed within, mark end time, and return
        ex.aggregate_child_materials()


        # End specializations
        for specialization in self.specializations:
            specialization.on_end(ex)

        return ex

    def executable_activity_nodes(
        self,
        ex: paml.ProtocolExecution,
        tokens: List[paml.ActivityEdgeFlow]
    ) -> List[uml.ActivityNode]:
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
            target = t.get_target()
            candidate_clusters[target] = candidate_clusters.get(target,[])+[t]
        return [n for n,nt in candidate_clusters.items()
                if n.enabled(ex, nt)]

    def execute_activity_node(self, ex : paml.ProtocolExecution, node: uml.ActivityNode,
                              tokens: List[paml.ActivityEdgeFlow]) -> List[paml.ActivityEdgeFlow]:
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
        # TODO change to pointer lookup after pySBOL #237
        # inputs are tokens that are either connected to node via an edge, or
        # are input pins connected to the node (implicitly) (i.e., the node owns the pin)
        # and the node identity is a prefix of the pin identity.
        inputs = [t for t in tokens if node == t.get_target()]
#                    if (hasattr(t, "edge") and t.edge and t.edge.lookup().target == node.identity) or \
#                       node.identity in t.token_source.lookup().node ]

        # Create a record for the node execution
        record = None
        new_tokens = []

        # Dispatch execution based on node type, collecting any object flows produced
        # The dispatch methods are the ones that can (or must be) overridden for a particular execution environment
        if isinstance(node, uml.InitialNode):
            non_call_edge_inputs = {i for i in inputs if i.edge.lookup() not in ex.activity_call_edge}
            if len(non_call_edge_inputs) != 0:
                raise ValueError(f'Initial node must have zero inputs, but {node.identity} had {len(inputs)}')
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
            # put a control token on all outgoing edges
        elif isinstance(node, uml.FlowFinalNode):
            # FlowFinalNode consumes tokens, but does not emit
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.FinalNode):
            # FinalNode completes the activity
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            calling_behavior_execution = self.get_calling_behavior_execution(record)
            if calling_behavior_execution and \
               calling_behavior_execution in self.blocked_nodes:


                # Map of subprotocol output parameter name to token
                subprotocol_output_tokens = {
                    t.token_source.lookup().node.lookup().parameter.lookup().property_value.name: t
                    for t in tokens
                    if isinstance(t.token_source.lookup().node.lookup(), uml.ActivityParameterNode) and
                    calling_behavior_execution == self.get_calling_behavior_execution(t.token_source.lookup())}

                # Out edges of calling behavior that need tokens corresponding to the
                # subprotocol output tokens
                calling_behavior_node = calling_behavior_execution.node.lookup()
                calling_behavior_out_edges = [
                    e for e in calling_behavior_node.protocol().edges
                      if calling_behavior_node == e.source.lookup() or
                         calling_behavior_node == e.source.lookup().get_parent()]

                #output_edges = {t: uml.ObjectFlow(source=t.node, target=calling_behavior_execution.output_pin(t.token_source.lookup().node.lookup().name)) for t in output_tokens}
                #ex.invocation_edges += output_edges
                new_tokens = [
                    paml.ActivityEdgeFlow(
                        token_source=(
                            subprotocol_output_tokens[e.source.lookup().name].token_source.lookup()
                            if isinstance(e, uml.ObjectFlow)
                            else calling_behavior_execution),
                        edge=e,
                        value=(
                            uml.literal(subprotocol_output_tokens[e.source.lookup().name].value, reference=True)
                            if isinstance(e, uml.ObjectFlow)
                            else uml.literal("uml.ControlFlow")))
                    for e in calling_behavior_out_edges
                ]
                ex.flows += new_tokens
                # Remove output_tokens from tokens (consumed by return from subprotocol)
                tokens = [t for t in tokens if t not in subprotocol_output_tokens.values()]
                self.blocked_nodes.remove(calling_behavior_execution)

            else:
                new_tokens = []

        elif isinstance(node, uml.ForkNode):
            if len(inputs) != 1:
                raise ValueError(f'Fork node must have precisely one input, but {node.identity} had {len(inputs)}')
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.JoinNode):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.MergeNode):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.DecisionNode):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.ActivityParameterNode):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            if node.parameter.lookup().property_value.direction == uml.PARAMETER_IN:
                new_tokens = self.next_tokens(record, ex)
            else:
                [value] = [i.value.value for i in inputs if isinstance(i.edge.lookup(), uml.ObjectFlow)]
                value = uml.literal(value, reference=True)
                ex.parameter_values += [paml.ParameterValue(parameter=node.parameter.lookup(), value=value)]
                new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.CallBehaviorAction):
            record = paml.CallBehaviorExecution(node=node, incoming_flows=inputs)

            # Get the parameter values from input tokens for input pins
            input_pin_values = {token.token_source.lookup().node.lookup():
                                     uml.literal(token.value, reference=True)
                                for token in inputs if not token.edge}

            # Get Input value pins
            value_pin_values = {}

            # Validate Pin values, see #130
            # Although enabled_activity_node method also validates Pin values,
            # it only checks required Pins.  This check is necessary to check optional Pins.
            for pin in node.inputs:
                if hasattr(pin, "value"):
                    if pin.value is None:
                        raise ValueError(f'{node.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}')
                    value_pin_values[pin.identity] = pin.value
            value_pin_values = {pin.identity: pin.value for pin in node.inputs if hasattr(pin, "value") and pin.value}

            # Convert References
            value_pin_values = {k: (uml.LiteralReference(value=ex.document.find(v.value))
                                    if isinstance(v.value, sbol3.refobj_property.ReferencedURI) or
                                       isinstance(v, uml.LiteralReference)
                                    else  uml.LiteralReference(value=v))
                                for k, v in value_pin_values.items()}
            pin_values = { **input_pin_values, **value_pin_values} # merge the dicts
            parameter_values = [paml.ParameterValue(parameter=node.pin_parameter(pin.name),
                                                    value=pin_values[pin])
                                for pin in node.inputs if pin in pin_values]
            parameter_values.sort(key=lambda x: ex.document.find(x.parameter).index)


            call = paml.BehaviorExecution(f"execute_{self.next_id()}",
                                          parameter_values=parameter_values,
                                          completed_normally=True,
                                          start_time=self.get_current_time(), # TODO: remove str wrapper after sbol_factory #22 fixed
                                          end_time=self.get_current_time(), # TODO: remove str wrapper after sbol_factory #22 fixed
                                          consumed_material=[]) # FIXME handle materials
            record.call = call

            ex.document.add(call)
            ex.executions.append(record)
            if isinstance(node.behavior.lookup(), paml.Protocol):
                # Push record onto blocked nodes to complete
                self.blocked_nodes.add(record)
                # new_tokens are those corresponding to the subprotocol initiating_nodes
                init_nodes = node.behavior.lookup().initiating_nodes()
                def get_invocation_edge(r, value_pin_values, n):
                    invocation = {}
                    value = None
                    if isinstance(n, uml.InitialNode):
                        try:
                            invocation['edge'] = uml.ControlFlow(source=r.node, target=n)
                            ex.activity_call_edge += [invocation['edge']]
                            source = next(i for i in r.incoming_flows
                                         if hasattr(i.lookup(), "edge") and
                                         i.lookup().edge and
                                         isinstance(i.lookup().edge.lookup(), uml.ControlFlow))
                            invocation['value'] = uml.literal(source.lookup().value, reference=True)

                        except StopIteration as e:
                            pass

                    elif isinstance(n, uml.ActivityParameterNode):
                        try:
                            try:
                                # if ActivityParameterNode is a ValuePin of the calling behavior, then it won't be an incoming flow
                                source = next(iter([v for v in value_pin_values if v.name == n.parameter.lookup().property_value.name]))
                                invocation['edge'] = uml.ObjectFlow(source=source, target=n)
                                ex.activity_call_edge += [invocation['edge']]
                                #ex.protocol.lookup().edges.append(invocation['edge'])
                                invocation['value'] = uml.literal(value_pin_values[source], reference=True)
                            except StopIteration as e:
                                source = next(iter([i for i in r.incoming_flows
                                    if i.lookup().token_source.lookup().node.lookup().name == n.parameter.lookup().property_value.name]))
                                invocation['edge'] = uml.ObjectFlow(source=source.lookup().token_source.lookup().node.lookup(), target=n)
                                ex.activity_call_edge += [invocation['edge']]
                                #ex.protocol.lookup().edges.append(invocation['edge'])
                                invocation['value'] = uml.literal(source.lookup().value, reference=True)
                        except StopIteration as e:
                            pass

                    return invocation

                new_tokens = [paml.ActivityEdgeFlow(token_source=record,
                                       **get_invocation_edge(record, value_pin_values, init_node))
                           for init_node in init_nodes ]
                ex.flows += new_tokens
            else:
                new_tokens = self.next_tokens(record, ex)

            ## Add the output values to the call parameter-values
            ### TODO: debug what happens when the same token name occurs more than once
            for token in new_tokens:
                edge = token.edge.lookup()
                if isinstance(edge, uml.ObjectFlow):
                    source = edge.source.lookup()
                    parameter = node.pin_parameter(source.name)
                    parameter_value = uml.literal(token.value, reference=True)
                    pv = paml.ParameterValue(parameter=parameter, value=parameter_value)
                    call.parameter_values += [pv]
            pin_names = [pv.parameter.lookup().property_value.name for pv in call.parameter_values]

        elif isinstance(node, uml.InputPin):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_pin_tokens(record, ex)
        elif isinstance(node, uml.OutputPin):
            record = paml.ActivityNodeExecution(node=node, incoming_flows=inputs)
            ex.executions.append(record)
            new_tokens = self.next_tokens(record, ex)
        elif isinstance(node, uml.OrderedPropertyValue):
            # node is an output parameter
            out_param = node
            [value] = [i.value for i in inputs] # Assume a single input for params
            param_value = paml.ParameterValue(parameter=out_param,
                                              value=uml.literal(value.value, reference=True))
            ex.parameter_values.append(param_value)
            new_tokens = self.next_tokens(record, ex)
        else:
            raise ValueError(f'Do not know how to execute node {node.identity} of type {node.type_uri}')

        if record:
            for specialization in self.specializations:

                # Execute node
                if isinstance(node, uml.CallBehaviorAction):

                    # Execute subprotocol
                    if isinstance(node.behavior.lookup(), paml.Protocol):
                        self.execute(node.behavior.lookup(),
                                     ex.association[0].agent.lookup(),
                                     id=f'{ex.display_id}{uuid.uuid4()}'.replace('-', '_'),
                                     parameter_values=[])
                try:
                    specialization.process(record, ex)
                except Exception as e:
                    l.error(f"Could Not Process {record.name if record.name else record.identity}: {e}")
                    if not failsafe:
                        l.error('Aborting...')
                        sys.exit(1)

        # return updated token list
        return [t for t in tokens if t not in inputs] + new_tokens

    def next_tokens(self, activity_node: paml.ActivityNodeExecution, ex: paml.ProtocolExecution):
        node = activity_node.node.lookup()
        protocol = node.protocol()
        out_edges = [e for e in protocol.edges
                     if activity_node.node == e.source or
                        activity_node.node == e.source.lookup().get_parent().identity]

        if isinstance(node, uml.ForkNode):
            [incoming_flow] = activity_node.incoming_flows
            incoming_value = incoming_flow.lookup().value
            edge_tokens = [paml.ActivityEdgeFlow(edge=edge, token_source=activity_node,
                                                 value=uml.literal(incoming_value, reference=True))
                           for edge in out_edges]
        elif isinstance(node, uml.DecisionNode):
            try:
                decision_input_flow_token = next(t for t in activity_node.incoming_flows if t.lookup().edge == node.decision_input_flow).lookup()
                decision_input_flow = decision_input_flow_token.edge.lookup()
                decision_input_value = decision_input_flow_token.value
            except StopIteration as e:
                decision_input_flow_token = None
                decision_input_value = None
                decision_input_flow = None
            try:
                decision_input_return_token = next(t for t in activity_node.incoming_flows if isinstance(t.lookup().edge.lookup().source.lookup(), uml.OutputPin) and t.lookup().token_source.lookup().node.lookup().behavior == node.decision_input).lookup()
                decision_input_return_flow = decision_input_return_token.edge.lookup()
                decision_input_return_value = decision_input_return_token.value
            except StopIteration as e:
                decision_input_return_token = None
                decision_input_return_value = None
                decision_input_return_flow = None

            try:
                primary_input_flow_token = next(t for t in activity_node.incoming_flows if t.lookup() != decision_input_flow_token and t.lookup() != decision_input_return_token).lookup()
                primary_input_flow = primary_input_flow_token.edge.lookup()
                primary_input_value = primary_input_flow_token.value
            except StopIteration as e:
                primary_input_value = None

            # Cases to evaluate guards of decision node:
            # 1. primary_input_flow is ObjectFlow, no decision_input, no decision_input_flow:
            #    Use primary_input_flow token to decide if guard is satisfied
            # 2. primary_input_flow is any, no decision_input, decision_input_flow present:
            #    Use decision_input_flow token to decide if guard is satisfied

            # 3. primary_input_flow is ControlFlow, decision_input present, no decision_input_flow:
            #    Use decision_input return value to decide if guard is satisfied (decision_input has no params)
            # 4. primary_input_flow is ControlFlow, decision_input present, decision_input_flow present:
            #    Use decision_input return value to decide if guard is satisfied (decision_input has decision_input_flow supplied parameter)

            # 5. primary_input_flow is ObjectFlow, decision_input present, no decision_input_flow:
            #    Use decision_input return value to decide if guard is satisfied (decision_input has primary_input_flow supplied parameter)
            # 6. primary_input_flow is ObjectFlow, decision_input present,  decision_input_flow present:
            #    Use decision_input return value to decide if guard is satisfied (decision_input has primary_input_flow and decision_input_flow supplied parameters)

            try:
                else_edge = next(edge for edge in out_edges if edge.guard.value == paml.DECISION_ELSE)
            except StopIteration as e:
                else_edge = None
            non_else_edges = [edge for edge in out_edges if edge != else_edge]

            def satisfy_guard(value, guard):
                if (value is None) or isinstance(value, uml.LiteralNull):
                    return (guard is None) or isinstance(guard, uml.LiteralNull)
                elif (guard is None) or isinstance(guard, uml.LiteralNull):
                    return False
                else:
                    return value.value == guard.value

            if hasattr(node, "decision_input") and node.decision_input:
                # Cases: 3, 4, 5, 6
                # The cases are combined because the cases refer to the inputs of the decision_input behavior
                # use decision_input_value to eval guards

                active_edges = [
                    edge for edge in non_else_edges
                    if satisfy_guard(decision_input_return_value, edge.guard)
                    ]
            else:
                # Cases: 1, 2
                if decision_input_flow:
                    # Case 2
                    # use decision_input_flow_token to eval guards

                    active_edges = [
                        edge for edge in non_else_edges
                        if satisfy_guard(decision_input_flow_token.value, edge.guard)
                    ]

                elif primary_input_flow and isinstance(primary_input_flow, uml.ObjectFlow):
                    # Case 1
                    # use primary_input_flow_token to eval guards
                    # Outgoing tokens are uml.ObjectFlow

                    active_edges = [
                        edge for edge in non_else_edges
                        if satisfy_guard(primary_input_flow_token.value, edge.guard)
                    ]
                else:
                    raise Exception("ERROR: Cannot evaluate DecisionNode with no decision_input, no decision_input_flow, and a None or uml.ControlFlow primary_input")

            assert(else_edge or len(active_edges) > 0)

            if len(active_edges) > 0:
                # FIXME always take first active edge, but could be different.
                active_edge = active_edges[0]
            else:
                active_edge = else_edge

            # Pick the value of the incoming_flow that corresponds to the primary_incoming edge
            edge_tokens = [paml.ActivityEdgeFlow(edge=active_edge, token_source=activity_node,
                                                 value=uml.literal(primary_input_value))]
        elif isinstance(node, uml.ActivityParameterNode) and \
             node.parameter.lookup().property_value.direction == uml.PARAMETER_IN:
            try:
                parameter_value = next(pv.value for pv in ex.parameter_values if pv.parameter == node.parameter)
            except StopIteration as e:
                try:
                    parameter_value = node.parameter.lookup().property_value.default_value
                except Exception as e:
                    raise Exception(f"ERROR: Could not find input parameter {node.parameter.lookup().property_value.name} value and/or no default_value.")
            edge_tokens = [paml.ActivityEdgeFlow(edge=edge, token_source=activity_node,
                                                 value=uml.literal(value=parameter_value, reference=True))
                           for edge in out_edges]
        elif isinstance(node, uml.ActivityParameterNode) and \
             node.parameter.lookup().property_value.direction == uml.PARAMETER_OUT:
            calling_behavior_execution = self.get_calling_behavior_execution(activity_node)
            if calling_behavior_execution:
                return_edge = uml.ObjectFlow(
                    source=node,
                    target=calling_behavior_execution.node.lookup().output_pin(node.parameter.lookup().property_value.name)
                )
                ex.activity_call_edge += [return_edge]
                edge_tokens = [
                    paml.ActivityEdgeFlow(
                        edge=return_edge,
                        token_source=activity_node,
                        value=self.get_value(activity_node, edge=return_edge)
                        #uml.literal(activity_node.incoming_flows[0].lookup().value)
                        )
                ]
            else:
                edge_tokens = []
        else:
            edge_tokens = [paml.ActivityEdgeFlow(edge=edge, token_source=activity_node,
                                                 value=self.get_value(activity_node, edge=edge))
                           for edge in out_edges]

        # Save tokens in the protocol execution
        ex.flows += edge_tokens

        # Assume that unlinked output pins are possible output parameters for the protocol
        if isinstance(activity_node, paml.CallBehaviorExecution):
            output_pins = activity_node.node.lookup().outputs
            unlinked_output_pins = [p for p in output_pins if p not in {e.source.lookup() for e in out_edges}]
            possible_output_parameter_values = [paml.ParameterValue(parameter=activity_node.node.lookup().pin_parameter(p.name),
                                                                    value=self.get_value(activity_node))
                                                for p in unlinked_output_pins]
            ex.parameter_values.extend(possible_output_parameter_values)
        return edge_tokens

    def get_value(self, activity_node : paml.CallBehaviorExecution, edge: uml.ActivityEdge = None):
        value = ""
        node = activity_node.node.lookup()
        reference = False
        if isinstance(edge, uml.ControlFlow):
            value = "uml.ControlFlow"
        elif isinstance(edge, uml.ObjectFlow):
            if isinstance(node, uml.ActivityParameterNode) and \
               node.parameter.lookup().property_value.direction == uml.PARAMETER_OUT:
                parameter = node.parameter.lookup().property_value
                value = activity_node.incoming_flows[0].lookup().value
                reference = True
            elif isinstance(node, uml.OutputPin):
                call_node = node.get_parent()
                parameter = call_node.pin_parameter(edge.source.lookup().name).property_value
                value = activity_node.incoming_flows[0].lookup().value
                reference = True
            else:
                parameter = node.pin_parameter(edge.source.lookup().name).property_value
                value = activity_node.compute_output(parameter)

        value = uml.literal(value, reference=reference)
        return value

    def next_pin_tokens(self, activity_node: paml.ActivityNodeExecution, ex: paml.ProtocolExecution):
        assert len(activity_node.incoming_flows) == 1 # One input per pin
        incoming_flow = activity_node.incoming_flows[0].lookup()
        pin_value = uml.literal(value=incoming_flow.value, reference=True)

        tokens = [ paml.ActivityEdgeFlow(edge=None, token_source=activity_node, value=pin_value) ]

        # Save tokens in the protocol execution
        ex.flows += tokens
        return tokens


    def execute_primitive(self, behavior: paml.Primitive, agent: sbol3.Agent, parameter_values: dict = {}, id: str = uuid.uuid4()) -> paml.BehaviorExecution:
        pass

    def get_calling_behavior_execution(self, activity_node: paml.ActivityNodeExecution):
        if activity_node in self.blocked_nodes:
            return activity_node
        else:
            for incoming_flow in activity_node.incoming_flows:
                parent_activity_node = incoming_flow.lookup().token_source.lookup()
                if parent_activity_node:
                    calling_behavior_execution = self.get_calling_behavior_execution(parent_activity_node)
                    return calling_behavior_execution
            return None

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


def protocol_execution_to_dot(self, execution_engine=None):
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
        value = incoming_flow.lookup().value
        value = value.value.lookup() if isinstance(value, uml.LiteralReference) else value.value

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

        edge_label = f"{src_var}-[{value}]->{dest_var}"
        attrs = {"color": "orange"}
        dot.edge(source_id, target_id, edge_label, _attributes=attrs)


    dot = graphviz.Digraph(name=f"cluster_{self.identity}",
                           graph_attr={
                               "label": self.identity
                           })

    # Protocol graph
    protocol_graph = self.document.find(self.protocol).to_dot()
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
