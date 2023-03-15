"""
The BehaviorExecution class defines the functions corresponding to the dynamically generated labop class BehaviorExecution
"""

import sbol3

import labop.inner as inner
from uml import Activity, LiteralSpecification


class BehaviorExecution(inner.BehaviorExecution, Activity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parameter_value_map(self):
        """
        Return a dictionary mapping parameter names to value or (value, unit)
        :param self:
        :return:
        """
        parameter_value_map = {}
        for pv in self.parameter_values:
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
                parameter_value_map[name] = {
                    "parameter": pv.parameter.lookup(),
                    "value": value,
                }
            else:
                if isinstance(parameter_value_map[name]["value"], list):
                    parameter_value_map[name]["value"] += [value]
                else:
                    parameter_value_map[name]["value"] = [
                        parameter_value_map[name]["value"],
                        value,
                    ]
        return parameter_value_map
