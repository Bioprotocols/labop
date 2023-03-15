"""
The ObjectFlow class defines the functions corresponding to the dynamically generated labop class ObjectFlow
"""

import uml.inner as inner
from uml.activity_edge import ActivityEdge


class ObjectFlow(inner.ObjectFlow, ActivityEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
