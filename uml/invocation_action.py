"""
The InvocationAction class defines the functions corresponding to the dynamically generated labop class InvocationAction
"""

from . import inner
from .action import Action


class InvocationAction(inner.InvocationAction, Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
