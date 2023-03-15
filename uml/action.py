"""
The Action class defines the functions corresponding to the dynamically generated labop class Action
"""

import uml.inner as inner
from uml.executable_node import ExecutableNode


class Action(inner.Action, ExecutableNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
