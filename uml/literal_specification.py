"""
The LiteralSpecification class defines the functions corresponding to the dynamically generated labop class LiteralSpecification
"""

import html

from . import inner
from .value_specification import ValueSpecification


class LiteralSpecification(inner.LiteralSpecification, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_value(self):
        return self.value

    def __str__(self):
        value = self.get_value()
        if isinstance(value, str) or isinstance(value, int) or isinstance(value, bool):
            val_str = html.escape(str(value)).lstrip("\n").replace("\n", "<br/>")
        else:
            val_str = str(value)
        return val_str
