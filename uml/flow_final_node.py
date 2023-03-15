"""
The FlowFinalNode class defines the functions corresponding to the dynamically generated labop class FlowFinalNode
"""

import uml.inner as inner
from uml.final_node import FinalNode


class FlowFinalNode(inner.FlowFinalNode, FinalNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
