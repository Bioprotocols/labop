"""
The Parameter class defines the functions corresponding to the dynamically generated labop class Parameter
"""


from typing import List

from uml import PARAMETER_IN, PARAMETER_OUT

from . import inner
from .utils import (
    WellFormednessInfo,
    WellFormednessIssue,
    WhereDefinedMixin,
    labop_hash,
)


class Parameter(inner.Parameter, WhereDefinedMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def __hash__(self) -> int:
        return labop_hash(self.identity)

    def is_output(self) -> bool:
        return self.direction == PARAMETER_OUT

    def is_input(self) -> bool:
        return self.direction == PARAMETER_IN

    def required(self) -> bool:
        return (
            hasattr(self, "lower_value")
            and self.lower_value
            and self.lower_value.get_value() > 0
        )

    def __str__(self):
        """
        Create a human readable string for a parameter.
        :param self:
        :return: str
        """
        default_value_str = f"= {self.default_value}" if self.default_value else ""
        return f"""{self.name}: {self.type} {default_value_str}"""

    def label(self) -> str:
        return f"{self.name}"

    def template(self) -> str:
        """
        Create a template for a parameter. Used for populating UI elements.
        :param self:
        :return: str
        """
        default_value_str = f"= {self.default_value}" if self.default_value else ""
        return f"""{self.name}=\'{default_value_str}\'"""

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A Parameter is well formed if:
        - warn about missing lower_value
        - no undefined default value
        - has a name
        """
        issues = []
        if not hasattr(self, "lower_value") or self.lower_value is None:
            issues += [
                WellFormednessInfo(
                    self,
                    f"Parameter.lower_value is not set.  It will be interpreted as being not required.",
                    suggestion="Assigning the Parameter.lower_value to 0 will also indicate it is not required (but will suppress this notification).  Assigning it to 1 or greater will make it a required parameter.",
                )
            ]

        if hasattr(self, "name") and (
            self.name is None or not isinstance(self.name, str)
        ):
            issues += [
                WellFormednessError(
                    self,
                    "Parameter.name is not a string",
                    suggestion="Assign Parameter.name to a string value.",
                )
            ]

        return issues
