"""
The Duration class defines the functions corresponding to the dynamically generated labop class Duration
"""

import uml.inner as inner
from uml.value_specification import ValueSpecification


class Duration(inner.Duration, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
