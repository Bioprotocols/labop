"""
The SBOLFactory class defines the functions corresponding to the dynamically generated labop class SBOLFactory
"""

import labop.inner as inner


class SBOLFactory(inner.SBOLFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
