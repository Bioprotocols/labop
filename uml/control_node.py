"""
The ControlNode class defines the functions corresponding to the dynamically generated labop class ControlNode
"""

import uml.inner as inner
from uml.activity_node import ActivityNode


class ControlNode(inner.ControlNode, ActivityNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
