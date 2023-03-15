"""
The ValuePin class defines the functions corresponding to the dynamically generated labop class ValuePin
"""

import uml.inner as inner
from uml.input_pin import InputPin


class ValuePin(inner.ValuePin, InputPin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_node_name(self):
        literal_str = self.value.dot_value()
        return f"{self.name}: {literal_str}"

    def __str__(self):
        return f"{self.name}: {self.value}"
