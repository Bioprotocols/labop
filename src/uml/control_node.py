"""
The ControlNode class defines the functions corresponding to the dynamically generated labop class ControlNode
"""

from . import inner
from .activity_node import ActivityNode


class ControlNode(inner.ControlNode, ActivityNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_parameter(self):
        return None
