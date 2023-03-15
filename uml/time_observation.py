"""
The TimeObservation class defines the functions corresponding to the dynamically generated labop class TimeObservation
"""

import uml.inner as inner
from uml.observation import Observation


class TimeObservation(inner.TimeObservation, Observation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
