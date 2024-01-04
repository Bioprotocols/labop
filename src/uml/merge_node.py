"""
The MergeNode class defines the functions corresponding to the dynamically generated labop class MergeNode
"""

from typing import Dict, List

from uml.literal_specification import LiteralSpecification

from . import inner
from .control_node import ControlNode


class MergeNode(inner.MergeNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(
        self,
        incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        return {"label": "", "shape": "diamond"}

    def enabled(
        self,
        edge_values: Dict["ActivityEdge", List[LiteralSpecification]],
        engine: "ExecutionEngine",
    ):
        protocol = self.protocol()
        return {t.edge.lookup() for t in tokens if t.edge} == protocol.incoming_edges(
            self
        )
