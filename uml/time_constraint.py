"""
The TimeConstraint class defines the functions corresponding to the dynamically generated labop class TimeConstraint
"""

from . import inner
from .interval_constraint import IntervalConstraint


class TimeConstraint(inner.TimeConstraint, IntervalConstraint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
