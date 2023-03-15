"""
The ActivityNode class defines the functions corresponding to the dynamically generated labop class ActivityNode
"""

import uml.inner as inner


class ActivityNode(inner.ActivityNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def unpin(self):
        """Find the root node for an ActivityNode: either itself if a Pin, otherwise the owning Action

        Parameters
        ----------
        self: ActivityNode

        Returns
        -------
        self if not a Pin, otherwise the owning Action
        """
        return self

    def dot_attrs(self):
        return {"label": "", "shape": "circle"}
