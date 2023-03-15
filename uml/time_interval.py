"""
The TimeInterval class defines the functions corresponding to the dynamically generated labop class TimeInterval
"""

import uml.inner as inner
from uml.interval import Interval


class TimeInterval(inner.TimeInterval, Interval):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
