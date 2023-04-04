"""
The FinalNode class defines the functions corresponding to the dynamically generated labop class FinalNode
"""

from typing import Callable, List

import uml
from uml.activity_edge import ActivityEdge

from . import inner
from .control_node import ControlNode


class FinalNode(inner.FinalNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {
            "label": "",
            "shape": "doublecircle",
            "style": "filled",
            "fillcolor": "black",
        }

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List[ActivityEdge],
        node_outputs: Callable,
    ) -> List["ActivityEdgeFlow"]:
        calling_behavior_execution = source.get_calling_behavior_execution()
        if calling_behavior_execution:
            new_tokens = calling_behavior_execution.complete_subprotocol(engine)
            return new_tokens
        else:
            return []
