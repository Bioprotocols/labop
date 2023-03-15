"""
The ControlFlow class defines the functions corresponding to the dynamically generated labop class ControlFlow
"""

import uml.inner as inner
from uml.activity_edge import ActivityEdge


class ControlFlow(inner.ControlFlow, ActivityEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
