"""
The ParameterValue class defines the functions corresponding to the dynamically generated labop class ParameterValue
"""

from typing import Dict, List, Union

import sbol3

import labop.inner as inner
from uml import LiteralSpecification, labop_hash


class ParameterValue(inner.ParameterValue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity)

    @staticmethod
    def parameter_value_map(
        parameter_values: List["ParameterValue"],
    ) -> Dict[str, Union[List[LiteralSpecification], LiteralSpecification]]:
        """
        Return a dictionary mapping parameter names to value or (value, unit)
        :param self:
        :return:
        """

        parameter_value_map = {}
        for pv in parameter_values:
            name = pv.parameter.lookup().property_value.name
            ref = pv.value

            # Done dereferencing, now get the actual parameter values
            if isinstance(ref, LiteralSpecification):
                value = ref.get_value()
            elif isinstance(ref, sbol3.Identified):
                value = ref
            else:
                raise TypeError(
                    f"Invalid value for Parameter {name} of type {type(ref)}"
                )

            # TODO: Refactor the parameter_value_map to better support
            # multi-valued parameters. However, refactoring will have
            # downstream effects on BehaviorSpecializations

            if name not in parameter_value_map:
                parameter_value_map[name] = [value]

            else:
                if isinstance(parameter_value_map[name], list):
                    parameter_value_map[name] += [value]
                else:
                    parameter_value_map[name] = [value]
        parameter_value_map = {
            k: (v[0] if len(v) == 1 else v) for k, v in parameter_value_map.items()
        }
        return parameter_value_map
