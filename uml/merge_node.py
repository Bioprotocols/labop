"""
The MergeNode class defines the functions corresponding to the dynamically generated labop class MergeNode
"""

import uml.inner as inner
from uml.control_node import ControlNode


class MergeNode(inner.MergeNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {"label": "", "shape": "diamond"}
