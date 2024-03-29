"""
The ControlFlow class defines the functions corresponding to the dynamically generated labop class ControlFlow
"""
from . import inner
from .activity_edge import ActivityEdge


class ControlFlow(inner.ControlFlow, ActivityEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def dot_color(self):
        return "blue"
