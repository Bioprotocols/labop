"""
The Pin class defines the functions corresponding to the dynamically generated labop class Pin
"""


from typing import Dict, List

from . import inner
from .object_node import ObjectNode
from .parameter import Parameter
from .utils import WellFormednessIssue


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

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A pin is well formed if:
        - it corresponds to a parameter
        """
        issues = []

        try:
            parameter = self.get_parent().pin_parameter(self.name)
            if parameter is None:
                issues += [
                    WellFormednessIssue(
                        self,
                        "Pin must correspond to a Parameter of the same name.",
                        "Report the issue at: https://github.com/Bioprotocols/labop/issues.",
                    )
                ]
        except Exception as e:
            issues += [
                WellFormednessIssue(
                    self,
                    "Could not find a Parameter corresponding to the Pin.",
                    WellFormednessIssue.REPORT_ISSUE,
                )
            ]
        return issues
