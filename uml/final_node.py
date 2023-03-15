"""
The FinalNode class defines the functions corresponding to the dynamically generated labop class FinalNode
"""

import uml.inner as inner
from uml.control_node import ControlNode


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
