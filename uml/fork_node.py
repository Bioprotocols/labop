"""
The ForkNode class defines the functions corresponding to the dynamically generated labop class ForkNode
"""

from typing import Callable, Dict, List

import uml
from uml.activity_edge import ActivityEdge
from uml.control_flow import ControlFlow
from uml.object_flow import ObjectFlow
from uml.utils import literal

from . import inner
from .control_node import ControlNode


class ForkNode(inner.ForkNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(
        selfincoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        return {
            "label": "",
            "shape": "rectangle",
            "height": "0.02",
            "style": "filled",
            "fillcolor": "black",
        }

    # def enabled(
    #     self,
    #     tokens: List["ActivityEdgeFlow"],
    #     permissive: bool = False,
    # ):
    #     protocol = self.protocol()
    #     incoming_controls = {
    #         e
    #         for e in protocol.incoming_edges(self)
    #         if isinstance(e, ControlFlow)
    #     }
    #     incoming_objects = {
    #         e
    #         for e in protocol.incoming_edges(self)
    #         if isinstance(e, ObjectFlow)
    #     }

    #     assert (len(incoming_controls) + len(incoming_objects)) == 1 and len(
    #         tokens
    #     ) < 2  # At least one flow and no more than one token

    #     # Need at least one incoming control token
    #     tokens_present = {
    #         t.edge.lookup() for t in tokens if t.edge
    #     } == incoming_objects

    #     return tokens_present

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List[ActivityEdge],
        node_outputs: Callable,
    ) -> List["ActivityEdgeFlow"]:
        [incoming_flow] = source.incoming_flows
        incoming_value = incoming_flow.lookup().value
        edge_tokens = [
            (
                edge,
                source,
                literal(incoming_value, reference=True),
            )
            for edge in out_edges
        ]
        return edge_tokens
