"""
The Pin class defines the functions corresponding to the dynamically generated labop class Pin
"""


from typing import Dict, List

from . import inner
from .object_node import ObjectNode
from .parameter import Parameter
from .utils import WellFormednessError, WellFormednessIssue


class Pin(inner.Pin, ObjectNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_parameter(self, ordered=False):
        action = self.get_parent()
        parameter = action.get_parameter(self.name, ordered=ordered)
        return parameter

    def dot_attrs(
        self,
        incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None,
    ):
        return {}

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A pin is well formed if:
        - it corresponds to a parameter
        """
        issues = []

        try:
            parameter = self.get_parent().get_parameter(self.name)
            if parameter is None:
                issues += [
                    WellFormednessError(
                        self,
                        "Pin must correspond to a Parameter of the same name.",
                    )
                ]
        except Exception as e:
            issues += [
                WellFormednessError(
                    self,
                    "Could not find a Parameter corresponding to the Pin.",
                )
            ]
        return issues
