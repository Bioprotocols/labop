"""
The ValuePin class defines the functions corresponding to the dynamically generated labop class ValuePin
"""

from typing import Dict, List

from uml.pin import Pin
from uml.utils import WellFormednessError, WellFormednessIssue

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
        engine: "ExecutionEngine",
    ):
        return self.value is not None or engine.permissive

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A ValuePin is well formed if:
        - super.is_well_formed()
        - it has a value
        """
        issues = Pin.is_well_formed(self)

        if not hasattr(self, "value") or self.value is None:
            issues += [
                WellFormednessError(
                    self, "ValuePin must have a value that is not None."
                )
            ]
        return issues
