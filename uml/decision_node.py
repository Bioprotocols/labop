"""
The DecisionNode class defines the functions corresponding to the dynamically generated labop class DecisionNode
"""

from typing import Callable, List

from . import inner
from .activity_edge import ActivityEdge
from .control_flow import ControlFlow
from .control_node import ControlNode
from .literal_null import LiteralNull
from .object_flow import ObjectFlow
from .object_node import ObjectNode
from .output_pin import OutputPin
from .strings import DECISION_ELSE
from .utils import literal


class DecisionNode(inner.DecisionNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {"label": "", "shape": "diamond"}

    def add_decision_output(self, protocol, guard, target):
        """Attach a guarded edge between DecisionNode and target.

        Args:
            protocol (Protocol): The protocol with the self DecisionNode.
            guard (primitive type): edge guard
            target (.ActivityNode): edge target
        """

        kwargs = {"source": self, "target": target}
        kwargs["guard"] = literal(guard)
        outgoing_edge = (
            ObjectFlow(**kwargs)
            if isinstance(self.get_primary_incoming_flow(protocol).source, ObjectNode)
            else ControlFlow(**kwargs)
        )
        protocol.edges.append(outgoing_edge)

    def get_primary_incoming_flow(self, protocol):
        try:
            primary_incoming_flow = next(
                e
                for e in protocol.edges
                if e.target is not None
                and e.target.lookup() == self
                and e != self.decision_input_flow
                and not (
                    isinstance(e.get_source(), OutputPin)
                    and e.get_source().get_parent().behavior == self.decision_input
                )
            )
            return primary_incoming_flow
        except StopIteration as e:
            raise Exception(
                f"Could not find primary_incoming edge for DecisionNode: {self.identity}"
            )

    def get_decision_input_node(self):
        if hasattr(self, "decision_input") and self.decision_input:
            return self.decision_input
        else:
            # primary input flow leads to decision
            primary_incoming_flow = self.get_primary_incoming_flow(self.protocol())
            return primary_incoming_flow.get_source().get_decision_input_node()

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
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
                t
                for t in tokens
                if isinstance(t.edge.lookup().get_source(), OutputPin)
                and t.edge.lookup().get_source().get_parent().behavior
                == self.decision_input
            )
        except StopIteration:
            pass

        decision_input_flow_token = None
        try:
            decision_input_flow_token = next(
                t for t in tokens if t.edge.lookup() == self.decision_input_flow
            )
        except StopIteration:
            pass

        if isinstance(primary_flow, ControlFlow):
            # Need either decision_input_flow (if no decision_input) or flow from decision_input
            if hasattr(self, "decision_input") and self.decision_input:
                # Get flow from decision_input return
                return primary_token is not None and decision_input_token is not None
            else:
                # Get flow from decision_input_flow
                return primary_token and decision_input_flow_token
        else:  # primary is an object flow
            if hasattr(self, "decision_input") and self.decision_input:
                # Get flow from decision_input return
                return decision_input_token
            else:
                # Get flow from primary
                return primary_token

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List[ActivityEdge],
        node_outputs: Callable,
    ) -> List["ActivityEdgeFlow"]:
        try:
            decision_input_flow_token = next(
                t
                for t in source.incoming_flows
                if t.lookup().edge == self.decision_input_flow
            ).lookup()
            decision_input_flow = decision_input_flow_token.edge.lookup()
            decision_input_value = decision_input_flow_token.value
        except StopIteration as e:
            decision_input_flow_token = None
            decision_input_value = None
            decision_input_flow = None
        try:
            decision_input_return_token = next(
                t
                for t in source.incoming_flows
                if isinstance(t.lookup().edge.lookup().get_source(), OutputPin)
                and t.lookup().token_source.lookup().node.lookup().behavior
                == self.decision_input
            ).lookup()
            decision_input_return_flow = decision_input_return_token.edge.lookup()
            decision_input_return_value = decision_input_return_token.value
        except StopIteration as e:
            decision_input_return_token = None
            decision_input_return_value = None
            decision_input_return_flow = None

        try:
            primary_input_flow_token = next(
                t
                for t in source.incoming_flows
                if t.lookup() != decision_input_flow_token
                and t.lookup() != decision_input_return_token
            ).lookup()
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
            else_edge = next(
                edge for edge in out_edges if edge.guard.value == DECISION_ELSE
            )
        except StopIteration as e:
            else_edge = None
        non_else_edges = [edge for edge in out_edges if edge != else_edge]

        def satisfy_guard(value, guard):
            if (value is None) or isinstance(value, LiteralNull):
                return (guard is None) or isinstance(guard, LiteralNull)
            elif (guard is None) or isinstance(guard, LiteralNull):
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
                edge
                for edge in non_else_edges
                if satisfy_guard(decision_input_return_value, edge.guard)
            ]
        else:
            # Cases: 1, 2
            if decision_input_flow:
                # Case 2
                # use decision_input_flow_token to eval guards

                active_edges = [
                    edge
                    for edge in non_else_edges
                    if satisfy_guard(decision_input_flow_token.value, edge.guard)
                ]

            elif primary_input_flow and isinstance(primary_input_flow, ObjectFlow):
                # Case 1
                # use primary_input_flow_token to eval guards
                # Outgoing tokens are ObjectFlow

                active_edges = [
                    edge
                    for edge in non_else_edges
                    if satisfy_guard(primary_input_flow_token.value, edge.guard)
                ]
            else:
                raise Exception(
                    "ERROR: Cannot evaluate DecisionNode with no decision_input, no decision_input_flow, and a None or ControlFlow primary_input"
                )

        assert else_edge or len(active_edges) > 0

        if len(active_edges) > 0:
            # FIXME always take first active edge, but could be different.
            active_edge = active_edges[0]
        else:
            active_edge = else_edge

        # Pick the value of the incoming_flow that corresponds to the primary_incoming edge
        edge_tokens = [
            (
                active_edge,
                source,
                literal(primary_input_value),
            )
        ]
        return edge_tokens
