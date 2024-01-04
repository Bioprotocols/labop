"""
The Observation class defines the functions corresponding to the dynamically generated labop class Observation
"""

from . import inner


class Observation(inner.Observation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
