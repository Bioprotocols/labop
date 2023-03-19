"""
The InitialNode class defines the functions corresponding to the dynamically generated labop class InitialNode
"""

from typing import List

from . import inner
from .control_node import ControlNode


class InitialNode(inner.InitialNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {
            "label": "",
            "shape": "circle",
            "style": "filled",
            "fillcolor": "black",
        }

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
    ):
        return len(tokens) == 1 and tokens[0].get_target() == self
