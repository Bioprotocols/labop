from abc import abstractmethod
from typing import List
import paml
import uml
import sbol3

@abstractmethod
def activity_node_enabled(
    self: uml.ActivityNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
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
        required_inputs = [self.input_pin(i.property_value.name)
                        for i in self.behavior.lookup().get_required_inputs()]
        required_value_pins = {p for p in required_inputs if isinstance(p, uml.ValuePin)}
        required_input_pins = {p for p in required_inputs if not isinstance(p, uml.ValuePin)}
        pins_with_tokens = {t.token_source.lookup().node.lookup() for t in tokens if not t.edge}
        # parameter_names = {pv.parameter.lookup().property_value.name for pv in ex.parameter_values}
        # pins_with_params = {p for p in required_input_pins if p.name in parameter_names}
        # satisfied_pins = set(list(pins_with_params) + list(pins_with_tokens))
        input_pins_satisfied = required_input_pins.issubset(pins_with_tokens)
        value_pins_assigned = all({i.value for i in required_value_pins})
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
    tokens: List[paml.ActivityEdgeFlow]
):
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}

    assert(len(incoming_controls) == 0) # Pins do not receive control flow
    assert(len(incoming_objects) > 0) # input pins have at least one object flow

    # Need at least one incoming object token
    tokens_present = {t.edge.lookup() for t in tokens if t.edge}.issubset(incoming_objects)

    return tokens_present
uml.InputPin.enabled = input_pin_enabled

def value_pin_enabled(
    self: uml.InputPin,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
):
    protocol = self.protocol()
    incoming_controls = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)}
    incoming_objects = {e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)}

    assert(len(incoming_controls) == 0 and len(incoming_objects)==0) # ValuePins do not receive flow

    return True
uml.ValuePin.enabled = value_pin_enabled

def output_pin_enabled(
    self: uml.InputPin,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
):
    return False
uml.OutputPin.enabled = output_pin_enabled


def fork_node_enabled(
    self: uml.ForkNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
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
    tokens: List[paml.ActivityEdgeFlow]
):
    protocol = self.protocol()
    token_present = any({t.edge.lookup() for t in tokens if t.edge}.intersection(protocol.incoming_edges(self)))
    return token_present
uml.FinalNode.enabled = final_node_enabled

def activity_parameter_node_enabled(
    self: uml.ActivityParameterNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
):
    return len(tokens) == 1 and tokens[0].get_target() == self
uml.ActivityParameterNode.enabled = activity_parameter_node_enabled

def initial_node_enabled(
    self: uml.InitialNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
):
    return len(tokens) == 1 and tokens[0].get_target() == self
uml.InitialNode.enabled = initial_node_enabled

def merge_node_enabled(
    self: uml.MergeNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
):
    protocol = self.protocol()
    return {t.edge.lookup() for t in tokens if t.edge}==protocol.incoming_edges(self)
uml.MergeNode.enabled = merge_node_enabled

def decision_node_enabled(
    self: uml.DecisionNode,
    ex: paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
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


def activity_node_execute(
    self: uml.ActivityNode,
    ee, # paml.ExecutionEngine
    ex : paml.ProtocolExecution,
    tokens: List[paml.ActivityEdgeFlow]
) -> List[paml.ActivityEdgeFlow]:
    """Execute a node in an activity, consuming the incoming flows and recording execution and outgoing flows

    Parameters
    ----------
    self: node to be executed
    ex: Current execution record
    ee: Execution Engine
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
    pass
uml.ActivityNode.execute = activity_node_execute

def backtrace(self, stack=None):
    stack = self.executions if stack is None else stack
    if len(stack) == 0:
        return ["<start>"]
    else:
        tail = stack[-1]
        head = stack[:-1]

        head_str = self.backtrace(stack=head)

        behavior_str = tail.node.lookup().behavior if isinstance(tail.node.lookup(), uml.CallBehaviorAction) else ((tail.node.lookup().get_parent().behavior, tail.node.lookup().name) if isinstance(tail.node.lookup(), uml.Pin) else "")
        tail_str = f"{tail.node} ({behavior_str})"

        head_str += [tail_str]
        return head_str
paml.ProtocolExecution.backtrace = backtrace

def token_info(self: paml.ActivityEdgeFlow):
    return {
        "edge_type": (type(self.edge) if self.edge else None),
        "source" : self.token_source.lookup().node.lookup().identity,
        "target": self.get_target().identity,
        "behavior": (self.get_target().behavior if isinstance(self.get_target(), uml.CallBehaviorAction) else None)
    }
paml.ActivityEdgeFlow.info = token_info
