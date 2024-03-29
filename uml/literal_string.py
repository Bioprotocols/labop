"""
The LiteralString class defines the functions corresponding to the dynamically generated labop class LiteralString
"""

from . import inner
from .literal_specification import LiteralSpecification


class LiteralString(inner.LiteralString, LiteralSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_value(self):
        return self.value
