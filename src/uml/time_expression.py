"""
The TimeExpression class defines the functions corresponding to the dynamically generated labop class TimeExpression
"""

from . import inner
from .value_specification import ValueSpecification


class TimeExpression(inner.TimeExpression, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
