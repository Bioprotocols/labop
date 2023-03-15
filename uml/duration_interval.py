"""
The DurationInterval class defines the functions corresponding to the dynamically generated labop class DurationInterval
"""

import uml.inner as inner
from uml.interval import Interval


class DurationInterval(inner.DurationInterval, Interval):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
