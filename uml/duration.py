"""
The Duration class defines the functions corresponding to the dynamically generated labop class Duration
"""

from . import inner
from .value_specification import ValueSpecification


class Duration(inner.Duration, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
