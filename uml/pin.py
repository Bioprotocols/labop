"""
The Pin class defines the functions corresponding to the dynamically generated labop class Pin
"""


from typing import Dict, List

from . import inner
from .object_node import ObjectNode


class Pin(inner.Pin, ObjectNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_parameter(self):
        action = self.get_parent()
        parameter = action.pin_parameter(self.name)
        return parameter

    def dot_attrs(
        self,
        incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        return {}
