"""
The Interval class defines the functions corresponding to the dynamically generated labop class Interval
"""

from . import inner
from .value_specification import ValueSpecification


class Interval(inner.Interval, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
