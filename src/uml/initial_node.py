"""
The InitialNode class defines the functions corresponding to the dynamically generated labop class InitialNode
"""

from typing import Dict, List

import graphviz

from uml.control_flow import ControlFlow

from . import inner
from .activity_edge import ActivityEdge
from .control_node import ControlNode
from .literal_specification import LiteralSpecification


class InitialNode(inner.InitialNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(
        self,
        incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        return {
            "label": "",
            "shape": "circle",
            "style": "filled",
            "fillcolor": "black",
        }

    def enabled(
        self,
        edge_values: Dict[ActivityEdge, List[LiteralSpecification]],
        engine: "ExecutionEngine",
    ):
        incoming_controls = {e for e in edge_values if isinstance(e, ControlFlow)}
        if len(incoming_controls) > 0:
            # Need all incoming control tokens
            control_tokens_present = all(
                [len(edge_values[ic]) > 0 for ic in incoming_controls]
            )
            return control_tokens_present
        else:
            return True  # Can execute an InitialNode node with no incoming controls (assuming its the top-level InitialNode)
