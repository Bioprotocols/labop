"""
The ValueSpecification class defines the functions corresponding to the dynamically generated labop class ValueSpecification
"""

from . import inner


class ValueSpecification(inner.ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
