"""
The ParameterValue class defines the functions corresponding to the dynamically generated labop class ParameterValue
"""

import labop.inner as inner


class ParameterValue(inner.ParameterValue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
