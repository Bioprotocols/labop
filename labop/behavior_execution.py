"""
The BehaviorExecution class defines the functions corresponding to the dynamically generated labop class BehaviorExecution
"""

import sbol3

import labop.inner as inner
from uml import Activity

from . import ParameterValue


class BehaviorExecution(inner.BehaviorExecution, Activity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parameter_value_map(self):
        return ParameterValue.parameter_value_map(self.parameter_values)
