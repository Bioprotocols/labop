"""
The FlowFinalNode class defines the functions corresponding to the dynamically generated labop class FlowFinalNode
"""


from . import inner
from .final_node import FinalNode


class FlowFinalNode(inner.FlowFinalNode, FinalNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
