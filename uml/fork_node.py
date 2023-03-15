"""
The ForkNode class defines the functions corresponding to the dynamically generated labop class ForkNode
"""

import uml.inner as inner
from uml.control_node import ControlNode


class ForkNode(inner.ForkNode, ControlNode):
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

    def get_decision_input_node(self):
        [fork_input_edge] = [
            e for e in self.protocol().edges if e.target.lookup() == self
        ]
        decision_input_node = fork_input_edge.source.lookup().get_decision_input_node()
        return decision_input_node
