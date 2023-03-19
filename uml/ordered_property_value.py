"""
The OrderedPropertyValue class defines the functions corresponding to the dynamically generated labop class OrderedPropertyValue
"""

from . import inner


class OrderedPropertyValue(inner.OrderedPropertyValue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
