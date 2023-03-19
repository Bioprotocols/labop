"""
The InputPin class defines the functions corresponding to the dynamically generated labop class InputPin
"""

from typing import Callable, List

from . import inner
from .control_flow import ControlFlow
from .object_flow import ObjectFlow
from .pin import Pin
from .utils import literal


class InputPin(inner.InputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_node_name(self):
        return self.name

    def dot_attrs(self):
        return {}

    def __str__(self):
        return self.name

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
    ):
        protocol = self.protocol()
        incoming_controls = {
            e for e in protocol.incoming_edges(self) if isinstance(e, ControlFlow)
        }
        incoming_objects = {
            e for e in protocol.incoming_edges(self) if isinstance(e, ObjectFlow)
        }

        assert len(incoming_controls) == 0  # Pins do not receive control flow

        # # Every incoming edge has a token

        tokens_present = all(
            [
                any(
                    [token.edge == in_edge.identity for token in tokens]
                )  # tokens going from pins to activity
                for in_edge in incoming_objects
            ]
        )  # in_edges are going into pins

        return tokens_present or engine.permissive

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List[ActivityEdge],
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
