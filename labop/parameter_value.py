"""
The ParameterValue class defines the functions corresponding to the dynamically generated labop class ParameterValue
"""

from typing import List

import sbol3

import labop.inner as inner
from uml import LiteralSpecification


class ParameterValue(inner.ParameterValue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def parameter_value_map(parameter_values: List["ParameterValue"]):
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
        return parameter_value_map
