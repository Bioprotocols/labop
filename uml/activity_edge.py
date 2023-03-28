"""
The ActivityEdge class defines the functions corresponding to the dynamically generated labop class ActivityEdge
"""

from . import inner


class ActivityEdge(inner.ActivityEdge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_source(self):
        return self.source.lookup() if self.source else self.source

    def get_target(self):
        return self.target.lookup() if self.target else self.target
