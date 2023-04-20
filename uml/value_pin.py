"""
The ValuePin class defines the functions corresponding to the dynamically generated labop class ValuePin
"""

from typing import Dict, List

from . import inner
from .input_pin import InputPin
from .literal_specification import LiteralSpecification


class ValuePin(inner.ValuePin, InputPin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_node_name(self):
        literal_str = self.value.dot_value()
        return f"{self.name}: {literal_str}"

    def __str__(self):
        return f"{self.name}: {self.value}"

    def enabled(
        self,
        edge_values: Dict["ActivityEdge", List[LiteralSpecification]],
        permissive=False,
    ):
        return self.value is not None or permissive
