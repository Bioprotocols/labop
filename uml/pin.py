"""
The Pin class defines the functions corresponding to the dynamically generated labop class Pin
"""


from . import inner
from .action import Action
from .object_node import ObjectNode


class Pin(inner.Pin, ObjectNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def unpin(self):
        """Find the root node for an ActivityNode: either itself if a Pin, otherwise the owning Action

        Parameters
        ----------
        self: Pin

        Returns
        -------
        self if not a Pin, otherwise the owning Action
        """
        action = self.get_parent()
        if not isinstance(action, Action):
            raise ValueError(
                f"Parent of {self.identity} should be Action, but found {type(action)} instead"
            )
        return action
