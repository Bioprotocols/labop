"""
The Expression class defines the functions corresponding to the dynamically generated labop class Expression
"""

from . import inner
from .value_specification import ValueSpecification


class Expression(inner.Expression, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
