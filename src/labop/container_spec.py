"""
The ContainerSpec class defines the functions corresponding to the dynamically generated labop class ContainerSpec
"""

from . import inner


class ContainerSpec(inner.ContainerSpec):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
