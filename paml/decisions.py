import paml
import uml
from typing import Dict, List, Tuple

def protocol_make_decision_node(
    self: paml.Protocol,
    primary_incoming_node: uml.ActivityNode,
    decision_input_behavior: uml.Behavior = None,
    decision_input_source: uml.ActivityNode = None,
    outgoing_targets: List[Tuple[uml.ValueSpecification, uml.ActivityNode]] = None
    ):
    """
    Make a uml:DecisionNode using optionally specified incoming and outgoing nodes.
    Returns a uml:DecisionNode and a set of edges connecting incoming and outgoing nodes.

    Args:
        primary_incoming_source_node (uml:ActivityNode): primary incoming edge type (control or object) determines output edge types
        decision_input_source_node (uml:ActivityNode, optional): Used to evaluate guards. Defaults to None.
        outgoing_targets (List[Tuple[uml.ValueSpecification, uml.ActivityNode]], optional): List of pairs of guards and nodes for outgoing edges. Defaults to None.
    """

    assert(primary_incoming_node)
    primary_incoming_flow = uml.ControlFlow(source=primary_incoming_node)
    self.edges.append(primary_incoming_flow)

    if decision_input_behavior:
        input_pin_map = {}
        decision_input_control = None
        if decision_input_source:
            input_pin_map["decision_input"] = decision_input_source
        if primary_incoming_node:
            if isinstance(primary_incoming_node, uml.ObjectNode):
                input_pin_map["primary_input"] = primary_incoming_node
            else:
                # Make a ControlFlow so that decision_input executes first
                decision_input_control = uml.ControlFlow(source=primary_incoming_node)

        decision_input = self.execute_primitive(decision_input_behavior, **input_pin_map)
        if decision_input_control:
            decision_input_control.target = decision_input
            self.edges.append(decision_input_control)

    decision_input_flow = None
    if decision_input_source:
        decision_input_flow = uml.ObjectFlow(source=decision_input_source)
        self.edges.append(decision_input_flow)

    decision = uml.DecisionNode(decision_input=decision_input_behavior,
                                decision_input_flow=decision_input_flow)
    self.nodes.append(decision)

    if decision_input:
        # Flow that communicates the return value of the decision_input behavior execution to the decision
        decision_input_to_decision_flow = uml.ObjectFlow(source=decision_input.output_pin("return"), target=decision)
        self.edges.append(decision_input_to_decision_flow)

    primary_incoming_flow.target = decision
    if decision_input_flow:
        decision_input_flow.target = decision

    # Make edges for outgoing_targets
    if outgoing_targets:
        for (guard, target) in outgoing_targets:
            assert((not guard) or isinstance(guard, uml.ValueSpecification))
            kwargs = { "source": decision, "target": target }
            if guard:
                kwargs["guard"] = guard
            outgoing_edge = uml.ObjectFlow(**kwargs) if \
                    isinstance(primary_incoming_node, uml.ObjectNode) else \
                    uml.ControlFlow(**kwargs)
            self.edges.append(outgoing_edge)


    return decision
paml.Protocol.make_decision_node = protocol_make_decision_node  # Add to class via monkey patch
