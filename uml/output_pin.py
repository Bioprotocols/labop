"""
The OutputPin class defines the functions corresponding to the dynamically generated labop class OutputPin
"""

import uml.inner as inner
from uml.pin import Pin


class OutputPin(inner.OutputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_decision_input_node(self):
        return self.get_parent()
