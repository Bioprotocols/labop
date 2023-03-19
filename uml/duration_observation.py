"""
The DurationObservation class defines the functions corresponding to the dynamically generated labop class DurationObservation
"""

from . import inner
from .observation import Observation


class DurationObservation(inner.DurationObservation, Observation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
