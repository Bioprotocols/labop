"""
The MergeNode class defines the functions corresponding to the dynamically generated labop class MergeNode
"""

from typing import List

from . import inner
from .control_node import ControlNode


class MergeNode(inner.MergeNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {"label": "", "shape": "diamond"}

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
    ):
        protocol = self.protocol()
        return {t.edge.lookup() for t in tokens if t.edge} == protocol.incoming_edges(
            self
        )
