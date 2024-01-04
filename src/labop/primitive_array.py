"""
The PrimitiveArray class defines the functions corresponding to the dynamically generated labop class PrimitiveArray
"""

from . import inner


class PrimitiveArray(inner.PrimitiveArray):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
