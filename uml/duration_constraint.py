"""
The DurationConstraint class defines the functions corresponding to the dynamically generated labop class DurationConstraint
"""

import uml.inner as inner
from uml.interval_constraint import IntervalConstraint


class DurationConstraint(inner.DurationConstraint, IntervalConstraint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
