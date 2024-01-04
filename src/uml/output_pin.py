"""
The OutputPin class defines the functions corresponding to the dynamically generated labop class OutputPin
"""


from . import inner
from .literal_specification import LiteralSpecification
from .pin import Pin
from .utils import literal


class OutputPin(inner.OutputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()
