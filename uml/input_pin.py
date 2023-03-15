"""
The InputPin class defines the functions corresponding to the dynamically generated labop class InputPin
"""

import uml.inner as inner
from uml.pin import Pin


class InputPin(inner.InputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_node_name(self):
        return self.name

    def dot_attrs(self):
        return {}

    def __str__(self):
        return self.name
