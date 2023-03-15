"""
The LiteralInteger class defines the functions corresponding to the dynamically generated labop class LiteralInteger
"""

import uml.inner as inner
from uml.literal_specification import LiteralSpecification


class LiteralInteger(inner.LiteralInteger, LiteralSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_value(self):
        return str(self.value)
