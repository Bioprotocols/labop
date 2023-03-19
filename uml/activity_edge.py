"""
The ActivityEdge class defines the functions corresponding to the dynamically generated labop class ActivityEdge
"""

from . import inner


class ActivityEdge(inner.ActivityEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def source(self):
        return self.source.lookup()

    def target(self):
        return self.target.lookup()
