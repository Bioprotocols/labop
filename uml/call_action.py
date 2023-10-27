"""
The CallAction class defines the functions corresponding to the dynamically generated labop class CallAction
"""

from . import inner
from .invocation_action import InvocationAction


class CallAction(inner.CallAction, InvocationAction):
    def __init__(self, *args, **kwargs):
        super(CallAction, self).__init__(*args, **kwargs)
