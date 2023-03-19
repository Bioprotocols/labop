"""
The Constraint class defines the functions corresponding to the dynamically generated labop class Constraint
"""
from . import inner


class Constraint(inner.Constraint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
