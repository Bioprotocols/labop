"""
The InputPin class defines the functions corresponding to the dynamically generated labop class InputPin
"""

from typing import Callable, Dict, List

import sbol3

from . import inner
from .activity_node import ActivityNode
from .literal_specification import LiteralSpecification
from .pin import Pin
from .utils import WellFormednessError, WellFormednessIssue, literal


class InputPin(inner.InputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def dot_node_name(self):
        return self.name

    def __str__(self):
        return self.name

    def enabled(
        self,
        edge_values: Dict["ActivityEdge", List[LiteralSpecification]],
        engine: "ExecutionEngine",
    ):
        # protocol = self.protocol()
        # Need all incoming control tokens
        control_tokens_present = ActivityNode.enabled(self, edge_values, engine)

        tokens_present = all(
            [len(edge_values[e]) > 0 for e in edge_values]
        )  # in_edges are going into pins

        return tokens_present or engine.permissive

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List["ActivityEdge"],
        node_outputs: Callable,
    ) -> List["ActivityEdgeFlow"]:
        assert len(source.incoming_flows) == len(
            engine.ex.protocol.lookup().incoming_edges(source.node.lookup())
        )
        incoming_flows = [f.lookup() for f in source.incoming_flows]
        pin_values = [
            literal(value=incoming_flow.value, reference=True)
            for incoming_flow in incoming_flows
        ]
        edge_tokens = [(None, source, pin_value) for pin_value in pin_values]
        return edge_tokens

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        An InputPin is well formed if:
        - super.is_well_formed()
        - it has an incoming ObjectFlow
        """
        from .object_flow import ObjectFlow

        issues = Pin.is_well_formed(self)

        action = self.get_parent()
        activity = action.get_parent()
        incoming_edges = activity.incoming_edges(self)

        if not any([e for e in incoming_edges if isinstance(e, ObjectFlow)]):
            issues += [
                WellFormednessError(
                    self,
                    "InputPin must have an incoming ObjectFlow edge to ensure that it can be assigned.",
                    suggestion="Ensure that the invocation of the associated Behavior assigns the value of the Parameter.",
                )
            ]
        return issues
