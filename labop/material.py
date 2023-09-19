"""
The Material class defines the functions corresponding to the dynamically generated labop class Material
"""

from . import inner


class Material(inner.Material):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
