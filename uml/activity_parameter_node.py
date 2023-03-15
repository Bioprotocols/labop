"""
The ActivityParameterNode class defines the functions corresponding to the dynamically generated labop class ActivityParameterNode
"""

import uml.inner as inner
from uml.object_node import ObjectNode


class ActivityParameterNode(inner.ActivityParameterNode, ObjectNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        label = self.parameter.lookup().name
        return {"label": label, "shape": "rectangle", "peripheries": "2"}
