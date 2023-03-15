"""
The Expression class defines the functions corresponding to the dynamically generated labop class Expression
"""

import uml.inner as inner
from uml.value_specification import ValueSpecification


class Expression(inner.Expression, ValueSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
