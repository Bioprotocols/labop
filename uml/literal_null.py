"""
The LiteralNull class defines the functions corresponding to the dynamically generated labop class LiteralNull
"""

from . import inner
from .literal_specification import LiteralSpecification


class LiteralNull(inner.LiteralNull, LiteralSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_value(self):
        return None
