from abc import abstractmethod
from typing import Callable, List, Set, Tuple
import uuid
import paml
from paml_convert.behavior_specialization import BehaviorSpecialization
import uml
import sbol3
import logging
from paml.execution_engine import ExecutionEngine

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

@abstractmethod
def activity_node_enabled(
    self: uml.ActivityNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    """Check whether all incoming edges have values defined by a token in tokens and that all value pin values are
        defined.

        Parameters
        ----------
        self: node to be executed
        tokens: current list of pending edge flows

        Returns
        -------
        bool if self is enabled
        """
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}


    # Need at least one incoming control token
    control_tokens = {t.edge.lookup() for t in tokens if t.edge}
    if len(incoming_controls) == 0:
        tokens_present = True
    else:
        tokens_present = len(control_tokens.intersection(incoming_controls)) > 0

    if hasattr(self, "inputs"):
        required_inputs = [p for i in self.behavior.lookup().get_required_inputs() for p in self.input_pins(i.property_value.name)]

        required_value_pins = {p for p in required_inputs if isinstance(p, uml.ValuePin)}
        # Validate values, see #120
        for pin in required_value_pins:
            if pin.value is None:
                raise ValueError(f'{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}')
        required_input_pins = {p for p in required_inputs if not isinstance(p, uml.ValuePin)}
        pins_with_tokens = {t.token_source.lookup().node.lookup() for t in tokens if not t.edge}
        # parameter_names = {pv.parameter.lookup().property_value.name for pv in ex.parameter_values}
        # pins_with_params = {p for p in required_input_pins if p.name in parameter_names}
        # satisfied_pins = set(list(pins_with_params) + list(pins_with_tokens))
        input_pins_satisfied = required_input_pins.issubset(pins_with_tokens)
        value_pins_assigned = all({i.value for i in required_value_pins})
        if permissive:
            return tokens_present
        else:
            return tokens_present and input_pins_satisfied and value_pins_assigned
    else:
        return tokens_present
uml.ActivityNode.enabled = activity_node_enabled

def activity_node_get_protocol(node: uml.ActivityNode) -> paml.Protocol:
    """Find protocol object that contains the node.

        Parameters
        ----------
        node: node in a protocol

        Returns
        -------
        protocol containing node
        """
    parent = node.get_parent()
    if isinstance(parent, paml.Protocol):
        return parent
    elif not isinstance(parent, sbol3.TopLevel):
        return parent.protocol()
    else:
        raise Exception(f"Cannot find protocol for node: {node}")
uml.ActivityNode.protocol = activity_node_get_protocol

def input_pin_enabled(
    self: uml.InputPin,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}

    assert(len(incoming_controls) == 0) # Pins do not receive control flow
    assert(len(incoming_objects) > 0) # input pins have at least one object flow

    # Need at least one incoming object token
    tokens_present = {t.edge.lookup() for t in tokens if t.edge}.issubset(incoming_objects)

    return tokens_present or permissive
uml.InputPin.enabled = input_pin_enabled

def value_pin_enabled(
    self: uml.InputPin,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}

    assert(len(incoming_controls) == 0 and len(incoming_objects)==0) # ValuePins do not receive flow

    return True or permissive
uml.ValuePin.enabled = value_pin_enabled

def output_pin_enabled(
    self: uml.InputPin,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    return False
uml.OutputPin.enabled = output_pin_enabled


def fork_node_enabled(
    self: uml.ForkNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}

    assert((len(incoming_controls) + len(incoming_objects)) == 1 and len(tokens) < 2) # At least one flow and no more than one token

    # Need at least one incoming control token
    tokens_present = {t.edge.lookup() for t in tokens if t.edge} == incoming_objects

    return tokens_present
uml.ForkNode.enabled = fork_node_enabled

def final_node_enabled(
    self: uml.FinalNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    protocol = self.protocol()
    token_present = any({t.edge.lookup() for t in tokens if t.edge}.intersection(protocol.incoming_edges(self)))
    return token_present
uml.FinalNode.enabled = final_node_enabled

def activity_parameter_node_enabled(
    self: uml.ActivityParameterNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    return len(tokens) == 1 and tokens[0].get_target() == self
uml.ActivityParameterNode.enabled = activity_parameter_node_enabled

def initial_node_enabled(
    self: uml.InitialNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    return len(tokens) == 1 and tokens[0].get_target() == self
uml.InitialNode.enabled = initial_node_enabled

def merge_node_enabled(
    self: uml.MergeNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    protocol = self.protocol()
    return {t.edge.lookup() for t in tokens if t.edge}==protocol.incoming_edges(self)
uml.MergeNode.enabled = merge_node_enabled

def decision_node_enabled(
    self: uml.DecisionNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow],
    permissive: bool
):
    # Cases:
    # - primary is control, input_flow, no decision_input
    # - primary is control, decision_input flow,
    # - primary is object, no decision_input
    # - primary is object, decision_input
    protocol = self.protocol()
    primary_flow = self.get_primary_incoming_flow(protocol)
    primary_token = None
    try:
        primary_token = next(t for t in tokens if t.edge.lookup() == primary_flow)
    except StopIteration:
        pass

    decision_input_token = None
    try:
        decision_input_token = next(
            t for t in tokens
            if isinstance(t.edge.lookup().source.lookup(), uml.OutputPin) and
                t.edge.lookup().source.lookup().get_parent().behavior == self.decision_input)
    except StopIteration:
        pass

    decision_input_flow_token = None
    try:
        decision_input_flow_token = next(
            t for t in tokens
            if t.edge.lookup() == self.decision_input_flow)
    except StopIteration:
        pass

    if isinstance(primary_flow, uml.ControlFlow):
        # Need either decision_input_flow (if no decision_input) or flow from decision_input
        if hasattr(self, "decision_input") and self.decision_input:
            # Get flow from decision_input return
            return primary_token is not None and decision_input_token is not None
        else:
            # Get flow from decision_input_flow
            return primary_token and decision_input_flow_token
    else: # primary is an object flow
        if hasattr(self, "decision_input") and self.decision_input:
            # Get flow from decision_input return
            return decision_input_token
        else:
            # Get flow from primary
            return primary_token
uml.DecisionNode.enabled = decision_node_enabled

class ProtocolExecutionExtractor():
    def extract(self, record: paml.ActivityNodeExecution):
        pass

    def extract(self, token: paml.ActivityEdgeFlow):
        pass

class JSONProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def __init__(self) -> None:
        super().__init__()
        self.extraction_map = {
            uml.CallBehaviorAction : self.extract_call_behavior_action
        }

    def extract_call_behavior_action(self, token: paml.ActivityEdgeFlow):
        return super().extract(token)

    def extract(self, record: paml.ActivityNodeExecution):
        behavior_str = record.node.lookup().behavior \
                        if isinstance(record.node.lookup(), uml.CallBehaviorAction) \
                        else ((record.node.lookup().get_parent().behavior, record.node.lookup().name) \
                            if isinstance(record.node.lookup(), uml.Pin)
                            else "")
        record_str = f"{record.node} ({behavior_str})"
        return record_str

class StringProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def extract(self, record: paml.ActivityNodeExecution):
        behavior_str = record.node.lookup().behavior \
                        if isinstance(record.node.lookup(), uml.CallBehaviorAction) \
                        else ((record.node.lookup().get_parent().behavior, record.node.lookup().name) \
                            if isinstance(record.node.lookup(), uml.Pin)
                            else "")
        record_str = f"{record.node} ({behavior_str})"
        return record_str

def backtrace(
    self,
    stack=None,
    extractor: ProtocolExecutionExtractor = None):
    stack = self.executions if stack is None else stack
    if len(stack) == 0:
        return set([]), []
    else:
        tail = stack[-1]
        head = stack[:-1]
        nodes, head = self.backtrace(stack=head)
        nodes.add(tail.node.lookup())
        head += [extractor.extract(tail)]
        return nodes, head
paml.ProtocolExecution.backtrace = backtrace

def token_info(self: paml.ActivityEdgeFlow):
    return {
        "edge_type": (type(self.edge.lookup()) if self.edge else None),
        "source" : self.token_source.lookup().node.lookup().identity,
        "target": self.get_target().identity,
        "behavior": (self.get_target().behavior if isinstance(self.get_target(), uml.CallBehaviorAction) else None)
    }
paml.ActivityEdgeFlow.info = token_info

def protocol_execution_to_json(self):
    """
    Convert Protocol Execution to JSON
    """
    p_json = self.backtrace(extractor=JSONProtocolExecutionExtractor())[1]
    return json.dumps(p_json)
paml.ProtocolExecution.to_json = protocol_execution_to_json



def activity_node_execute(
    self: uml.ActivityNode,
    engine: ExecutionEngine,
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    """Execute a node in an activity, consuming the incoming flows and recording execution and outgoing flows

        Parameters
        ----------
        self: node to be executed
        engine: execution engine (for execution state and side-effects)

        Returns
        -------
        updated list of pending edge flows
    """
    # Extract the relevant set of incoming flow values
    inputs = [t for t in engine.tokens if self == t.get_target()]

    record = self.execute_callback(engine, inputs)
    engine.ex.executions.append(record)
    new_tokens = record.next_tokens(engine, node_outputs=node_outputs)

    if record:
        for specialization in engine.specializations:
            try:
                specialization.process(record, engine.ex)
            except Exception as e:
                l.error(f"Could Not Process {record.name if record.name else record.identity}: {e}")
                if not engine.failsafe:
                    l.error('Aborting...')
                    sys.exit(1)

    # return updated token list
    return [t for t in engine.tokens if t not in inputs] + new_tokens
uml.ActivityNode.execute = activity_node_execute


@abstractmethod
def activity_node_execute_callback(
    self: uml.ActivityNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    raise ValueError(f'Do not know how to execute node {self.identity} of type {self.type_uri}')
uml.ActivityNode.execute_callback = activity_node_execute_callback

def activity_node_execution_next_tokens(
    self: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    node = self.node.lookup()
    protocol = node.protocol()
    out_edges = [
        e for e in protocol.edges
        if self.node == e.source or
           self.node == e.source.lookup().get_parent().identity
        ]

    edge_tokens = node.next_tokens_callback(self, engine, out_edges, node_outputs=node_outputs)

    if edge_tokens:
        # Save tokens in the protocol execution
        engine.ex.flows += edge_tokens
    else:
        pass

    # # Assume that unlinked output pins are possible output parameters for the protocol
    # if isinstance(self, paml.CallBehaviorExecution):
    #     output_pins = self.node.lookup().outputs
    #     unlinked_output_pins = [p for p in output_pins if p not in {e.source.lookup() for e in out_edges}]
    #     possible_output_parameter_values = [paml.ParameterValue(parameter=self.node.lookup().pin_parameter(p.name),
    #                                                             value=self.get_value())
    #                                         for p in unlinked_output_pins]
    #     engine.ex.parameter_values.extend(possible_output_parameter_values)
    return edge_tokens
paml.ActivityNodeExecution.next_tokens = activity_node_execution_next_tokens

def activity_node_next_tokens_callback(
    self: uml.ActivityNode,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    edge_tokens = [
        paml.ActivityEdgeFlow(
            edge=edge,
            token_source=source,
            value=source.get_value(edge=edge, node_outputs=node_outputs)
            )
        for edge in out_edges]
    return edge_tokens
uml.ActivityNode.next_tokens_callback = activity_node_next_tokens_callback

def activity_node_execution_get_value(
    self : paml.ActivityNodeExecution,
    edge: uml.ActivityEdge = None,
    node_outputs: Callable = None
):
    value = ""
    node = self.node.lookup()
    reference = False

    if isinstance(edge, uml.ControlFlow):
        value = "uml.ControlFlow"
    elif isinstance(edge, uml.ObjectFlow):
        if isinstance(node, uml.ActivityParameterNode) and \
            node.parameter.lookup().property_value.direction == uml.PARAMETER_OUT:
            parameter = node.parameter.lookup().property_value
            value = self.incoming_flows[0].lookup().value
            reference = True
        elif isinstance(node, uml.OutputPin):
            call_node = node.get_parent()
            parameter = call_node.pin_parameter(edge.source.lookup().name).property_value
            value = self.incoming_flows[0].lookup().value
            reference = True
        else:
            parameter = node.pin_parameter(edge.source.lookup().name).property_value
            if node_outputs:
                value = node_outputs(self, parameter)
            elif hasattr(self.node.lookup().behavior.lookup(), "compute_output"):
                value = self.compute_output(parameter)
            else:
                value = f"{parameter.name}"

    value = uml.literal(value, reference=reference)
    return value
paml.ActivityNodeExecution.get_value = activity_node_execution_get_value


def initial_node_execute_callback(
    self: uml.InitialNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:

    non_call_edge_inputs = {i for i in inputs if i.edge.lookup() not in engine.ex.activity_call_edge}
    if len(non_call_edge_inputs) != 0:
        raise ValueError(f'Initial node must have zero inputs, but {self.identity} had {len(inputs)}')
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)

    return record
uml.InitialNode.execute_callback = initial_node_execute_callback


def flow_final_node_execute_callback(
    self: uml.FlowFinalNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    # FlowFinalNode consumes tokens, but does not emit
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.FlowFinalNode.execute_callback = flow_final_node_execute_callback


def get_calling_behavior_execution(
    self: paml.ActivityNodeExecution,
    visited: Set[paml.ActivityNodeExecution] = None
) -> paml.ActivityNodeExecution:
    """Look for the InitialNode for the Activity including self and identify a Calling CallBehaviorExecution (if present)

    Args:
        self (paml.ActivityNodeExecution): current search node

    Returns:
        paml.CallBehaviorExecution: CallBehaviorExecution
    """
    node = self.node.lookup()
    if visited is None:
        visited = set({})
    if isinstance(node, uml.InitialNode):
        # Check if there is a CallBehaviorExecution incoming_flow
        try:
            caller = next(n.lookup().token_source.lookup() for n in self.incoming_flows if isinstance(n.lookup().token_source.lookup(), paml.CallBehaviorExecution))
        except StopIteration:
            return None
        return caller
    else:
        for incoming_flow in self.incoming_flows:
            parent_activity_node = incoming_flow.lookup().token_source.lookup()
            if parent_activity_node and (parent_activity_node not in visited) and \
                parent_activity_node.node.lookup().protocol() == node.protocol():
                visited.add(parent_activity_node)
                calling_behavior_execution = parent_activity_node.get_calling_behavior_execution(visited=visited)
                if calling_behavior_execution:
                    return calling_behavior_execution
        return None
paml.ActivityNodeExecution.get_calling_behavior_execution = get_calling_behavior_execution

def final_node_execute_callback(
    self: uml.FinalNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    # FinalNode completes the activity
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.FinalNode.execute_callback = final_node_execute_callback

def final_node_next_tokens_callback(
    self: uml.FinalNode,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    calling_behavior_execution = source.get_calling_behavior_execution()
    if calling_behavior_execution:
        # and \
        # calling_behavior_execution in self.blocked_nodes:


        # Map of subprotocol output parameter name to token
        subprotocol_output_tokens = {
            t.token_source.lookup().node.lookup().parameter.lookup().property_value.name: t
            for t in engine.tokens
            if isinstance(t.token_source.lookup().node.lookup(), uml.ActivityParameterNode) and
               calling_behavior_execution == t.token_source.lookup().get_calling_behavior_execution()}

        # Out edges of calling behavior that need tokens corresponding to the
        # subprotocol output tokens
        calling_behavior_node = calling_behavior_execution.node.lookup()
        calling_behavior_out_edges = [
            e for e in calling_behavior_node.protocol().edges
                if calling_behavior_node == e.source.lookup() or
                    calling_behavior_node == e.source.lookup().get_parent()]

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
        # engine.ex.flows += new_tokens
        # Remove output_tokens from tokens (consumed by return from subprotocol)
        engine.tokens = [t for t in engine.tokens if t not in subprotocol_output_tokens.values()]
        engine.blocked_nodes.remove(calling_behavior_execution)
        return new_tokens
    else:
        return []
uml.FinalNode.next_tokens_callback = final_node_next_tokens_callback


def fork_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    if len(inputs) != 1:
        raise ValueError(f'Fork node must have precisely one input, but {self.identity} had {len(inputs)}')
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.ForkNode.execute_callback = fork_node_execute_callback

def fork_node_next_tokens_callback(
    self: uml.ForkNode,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    [incoming_flow] = source.incoming_flows
    incoming_value = incoming_flow.lookup().value
    edge_tokens = [
        paml.ActivityEdgeFlow(
            edge=edge,
            token_source=source,
            value=uml.literal(incoming_value, reference=True))
        for edge in out_edges
    ]
    return edge_tokens
uml.ForkNode.next_tokens_callback = fork_node_next_tokens_callback

def control_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.ControlNode.execute_callback = control_node_execute_callback


def fork_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    if len(inputs) != 1:
        raise ValueError(f'Fork node must have precisely one input, but {self.identity} had {len(inputs)}')
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.ForkNode.execute_callback = fork_node_execute_callback

def decision_node_next_tokens_callback(
    self: uml.DecisionNode,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    try:
        decision_input_flow_token = next(t for t in source.incoming_flows if t.lookup().edge == self.decision_input_flow).lookup()
        decision_input_flow = decision_input_flow_token.edge.lookup()
        decision_input_value = decision_input_flow_token.value
    except StopIteration as e:
        decision_input_flow_token = None
        decision_input_value = None
        decision_input_flow = None
    try:
        decision_input_return_token = next(t for t in source.incoming_flows if isinstance(t.lookup().edge.lookup().source.lookup(), uml.OutputPin) and t.lookup().token_source.lookup().node.lookup().behavior == self.decision_input).lookup()
        decision_input_return_flow = decision_input_return_token.edge.lookup()
        decision_input_return_value = decision_input_return_token.value
    except StopIteration as e:
        decision_input_return_token = None
        decision_input_return_value = None
        decision_input_return_flow = None

    try:
        primary_input_flow_token = next(t for t in source.incoming_flows if t.lookup() != decision_input_flow_token and t.lookup() != decision_input_return_token).lookup()
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
        else_edge = next(edge for edge in out_edges if edge.guard.value == uml.DECISION_ELSE)
    except StopIteration as e:
        else_edge = None
    non_else_edges = [edge for edge in out_edges if edge != else_edge]

    def satisfy_guard(value, guard):
        if (value is None) or isinstance(value, uml.LiteralNull):
            return (guard is None) or isinstance(guard, uml.LiteralNull)
        elif (guard is None) or isinstance(guard, uml.LiteralNull):
            return False
        else:
            if isinstance(value.value, str):
                return value.value == str(guard.value)
            else:
                return value.value == guard.value

    if hasattr(self, "decision_input") and self.decision_input:
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
    edge_tokens = [paml.ActivityEdgeFlow(edge=active_edge, token_source=source,
                                            value=uml.literal(primary_input_value))]
    return edge_tokens
uml.DecisionNode.next_tokens_callback = decision_node_next_tokens_callback


def activity_parameter_node_execute_callback(
    self: uml.ActivityParameterNode,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    if self.parameter.lookup().property_value.direction == uml.PARAMETER_OUT:
        [value] = [i.value.value for i in inputs if isinstance(i.edge.lookup(), uml.ObjectFlow)]
        value = uml.literal(value, reference=True)
        engine.ex.parameter_values += [paml.ParameterValue(parameter=self.parameter.lookup(), value=value)]
    return record
uml.ActivityParameterNode.execute_callback = activity_parameter_node_execute_callback

def activity_parameter_node_next_tokens_callback(
    self: uml.ActivityParameterNode,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    if self.parameter.lookup().property_value.direction == uml.PARAMETER_IN:
        try:
            parameter_value = next(pv.value for pv in engine.ex.parameter_values if pv.parameter == self.parameter)
        except StopIteration as e:
            try:
                parameter_value = self.parameter.lookup().property_value.default_value
            except Exception as e:
                raise Exception(f"ERROR: Could not find input parameter {self.parameter.lookup().property_value.name} value and/or no default_value.")
        edge_tokens = [paml.ActivityEdgeFlow(edge=edge, token_source=source,
                                                value=uml.literal(value=parameter_value, reference=True))
                        for edge in out_edges]
    else:
        calling_behavior_execution = source.get_calling_behavior_execution()
        if calling_behavior_execution:
            return_edge = uml.ObjectFlow(
                source=self,
                target=calling_behavior_execution.node.lookup().output_pin(self.parameter.lookup().property_value.name)
            )
            engine.ex.activity_call_edge += [return_edge]
            edge_tokens = [
                paml.ActivityEdgeFlow(
                    edge=return_edge,
                    token_source=source,
                    value=source.get_value(edge=return_edge)
                    #uml.literal(source.incoming_flows[0].lookup().value)
                    )
            ]
        else:
            edge_tokens = []
    return edge_tokens
uml.ActivityParameterNode.next_tokens_callback = activity_parameter_node_next_tokens_callback

def call_behavior_action_execute_callback(
    self: uml.CallBehaviorAction,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    record = paml.CallBehaviorExecution(node=self, incoming_flows=inputs)

    # Get the parameter values from input tokens for input pins
    input_pin_values = {token.token_source.lookup().node.lookup():
                                uml.literal(token.value, reference=True)
                        for token in inputs if not token.edge}
    # Get Input value pins
    value_pin_values = {}

    # Validate Pin values, see #130
    # Although enabled_activity_node method also validates Pin values,
    # it only checks required Pins.  This check is necessary to check optional Pins.
    for pin in self.inputs:
        if hasattr(pin, "value"):
            if pin.value is None:
                raise ValueError(f'{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}')
            value_pin_values[pin.identity] = pin.value
    value_pin_values = {pin.identity: pin.value for pin in self.inputs if hasattr(pin, "value") and pin.value}

    # Convert References
    value_pin_values = {k: (uml.LiteralReference(value=engine.ex.document.find(v.value))
                            if isinstance(v.value, sbol3.refobj_property.ReferencedURI) or
                                isinstance(v, uml.LiteralReference)
                            else  uml.LiteralReference(value=v))
                        for k, v in value_pin_values.items()}
    pin_values = { **input_pin_values, **value_pin_values} # merge the dicts

    parameter_values = [paml.ParameterValue(parameter=self.pin_parameter(pin.name),
                                            value=pin_values[pin])
                        for pin in self.inputs if pin in pin_values]
    parameter_values.sort(key=lambda x: engine.ex.document.find(x.parameter).index)
    call = paml.BehaviorExecution(f"execute_{engine.next_id()}",
                                    parameter_values=parameter_values,
                                    completed_normally=True,
                                    start_time=engine.get_current_time(), # TODO: remove str wrapper after sbol_factory #22 fixed
                                    end_time=engine.get_current_time(), # TODO: remove str wrapper after sbol_factory #22 fixed
                                    consumed_material=[]) # FIXME handle materials
    record.call = call

    engine.ex.document.add(call)

    return record
uml.CallBehaviorAction.execute_callback = call_behavior_action_execute_callback

def call_behavior_action_next_tokens_callback(
    self: uml.CallBehaviorAction,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
) -> List[paml.ActivityEdgeFlow]:
    if isinstance(self.behavior.lookup(), paml.Protocol):
        if engine.is_asynchronous:
            # Push record onto blocked nodes to complete
            engine.blocked_nodes.add(source)
            # new_tokens are those corresponding to the subprotocol initiating_nodes
            init_nodes = self.behavior.lookup().initiating_nodes()
            def get_invocation_edge(r, n):
                invocation = {}
                value = None
                if isinstance(n, uml.InitialNode):
                    try:
                        invocation['edge'] = uml.ControlFlow(source=r.node, target=n)
                        engine.ex.activity_call_edge += [invocation['edge']]
                        source = next(i for i in r.incoming_flows
                                        if hasattr(i.lookup(), "edge") and
                                        i.lookup().edge and
                                        isinstance(i.lookup().edge.lookup(), uml.ControlFlow))
                        invocation['value'] = uml.literal(source.lookup().value, reference=True)

                    except StopIteration as e:
                        pass

                elif isinstance(n, uml.ActivityParameterNode):
                    # if ActivityParameterNode is a ValuePin of the calling behavior, then it won't be an incoming flow
                    source = self.input_pin(n.parameter.lookup().property_value.name)
                    invocation['edge'] = uml.ObjectFlow(source=source, target=n)
                    engine.ex.activity_call_edge += [invocation['edge']]
                    #ex.protocol.lookup().edges.append(invocation['edge'])
                    if isinstance(source, uml.ValuePin):
                        invocation['value'] = uml.literal(source.value, reference=True)
                    else:
                        try:
                            source = next(iter([i for i in r.incoming_flows
                                if i.lookup().token_source.lookup().node.lookup().name == n.parameter.lookup().property_value.name]))
                            # invocation['edge'] = uml.ObjectFlow(source=source.lookup().token_source.lookup().node.lookup(), target=n)
                            # engine.ex.activity_call_edge += [invocation['edge']]
                            #ex.protocol.lookup().edges.append(invocation['edge'])
                            invocation['value'] = uml.literal(source.lookup().value, reference=True)
                        except StopIteration as e:
                            pass

                return invocation

            new_tokens = [paml.ActivityEdgeFlow(token_source=source,
                                    **get_invocation_edge(source, init_node))
                        for init_node in init_nodes ]
            # engine.ex.flows += new_tokens
        else: # is synchronous execution
            # Execute subprotocol
            self.execute(self.behavior.lookup(),
                            engine.ex.association[0].agent.lookup(),
                            id=f'{engine.display_id}{uuid.uuid4()}'.replace('-', '_'),
                            parameter_values=[])
    else:
        new_tokens = uml.ActivityNode.next_tokens_callback(self, source, engine, out_edges, node_outputs=node_outputs)
    return new_tokens
uml.CallBehaviorAction.next_tokens_callback = call_behavior_action_next_tokens_callback

def pin_execute_callback(
    self: uml.Pin,
    engine: ExecutionEngine,
    inputs: List[paml.ActivityEdgeFlow]
) -> paml.ActivityNodeExecution:
    record = paml.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record
uml.Pin.execute_callback = pin_execute_callback

def input_pin_next_tokens_callback(
    self: uml.InputPin,
    source: paml.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable = None
    ) -> List[paml.ActivityEdgeFlow]:
    assert len(source.incoming_flows) == 1 # One input per pin
    incoming_flow = source.incoming_flows[0].lookup()
    pin_value = uml.literal(value=incoming_flow.value, reference=True)
    edge_tokens = [ paml.ActivityEdgeFlow(edge=None, token_source=source, value=pin_value) ]
    return edge_tokens
uml.InputPin.next_tokens_callback = input_pin_next_tokens_callback
