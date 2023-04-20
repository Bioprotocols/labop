"""
The ExecutableNode class defines the functions corresponding to the dynamically generated labop class ExecutableNode
"""

from typing import Dict, List

from . import inner
from .activity_node import ActivityNode


class ExecutableNode(inner.ExecutableNode, ActivityNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(
        self,
        incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        raise ValueError(f"Do not know what GraphViz label to use for {self}")
