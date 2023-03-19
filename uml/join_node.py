"""
The JoinNode class defines the functions corresponding to the dynamically generated labop class JoinNode
"""

from . import inner


class JoinNode(inner.JoinNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {
            "label": "",
            "shape": "rectangle",
            "height": "0.02",
            "style": "filled",
            "fillcolor": "black",
        }
