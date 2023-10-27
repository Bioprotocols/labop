"""
The TimeInterval class defines the functions corresponding to the dynamically generated labop class TimeInterval
"""

from . import inner
from .interval import Interval


class TimeInterval(inner.TimeInterval, Interval):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
