"""
The BehaviorExecution class defines the functions corresponding to the dynamically generated labop class BehaviorExecution
"""

from typing import Dict, List, Union

from uml import Activity, LiteralSpecification

from . import ParameterValue, inner


class BehaviorExecution(inner.BehaviorExecution, Activity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parameter_value_map(
        self,
    ) -> Dict[str, Union[List[LiteralSpecification], LiteralSpecification]]:
        return ParameterValue.parameter_value_map(self.parameter_values)
