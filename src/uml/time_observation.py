"""
The TimeObservation class defines the functions corresponding to the dynamically generated labop class TimeObservation
"""

from . import inner
from .observation import Observation


class TimeObservation(inner.TimeObservation, Observation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
