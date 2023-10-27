"""
The DurationInterval class defines the functions corresponding to the dynamically generated labop class DurationInterval
"""

from . import inner
from .interval import Interval


class DurationInterval(inner.DurationInterval, Interval):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
