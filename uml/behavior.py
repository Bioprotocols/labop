"""
The Behavior class defines the functions corresponding to the dynamically generated labop class Behavior
"""

from typing import Iterable

import uml.inner as inner
from uml.ordered_property_value import OrderedPropertyValue
from uml.parameter import Parameter
from uml.strings import PARAMETER_IN, PARAMETER_OUT
from uml.utils import literal
from uml.value_specification import ValueSpecification


class Behavior(inner.Behavior):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_parameter(
        self,
        name: str,
        param_type: str,
        direction: str,
        optional: bool = False,
        unbounded: bool = False,
        default_value: ValueSpecification = None,
    ) -> OrderedPropertyValue:
        """Add a Parameter for this Behavior; usually not called directly

        Note: Current assumption is that cardinality is either [0..1] or 1
        :param name: name of the parameter, which will also be used for pins
        :param param_type: URI specifying the type of object that is expected for this parameter
        :param direction: should be in or out
        :param optional: True if the Parameter is optional; default is False
        :param default_value: must be specified if Parameter is optional
        :return: Parameter that has been added
        """
        param = Parameter(
            name=name,
            type=param_type,
            direction=direction,
            is_ordered=True,
            is_unique=True,
        )
        ordered_param = OrderedPropertyValue(
            index=len(self.parameters), property_value=param
        )
        self.parameters.append(ordered_param)

        # Leave upper value property unspecified if the Parameter supports
        # an unbounded number of ParameterValues
        if not unbounded:
            param.upper_value = literal(1)
        if optional:
            param.lower_value = literal(0)
        else:
            param.lower_value = literal(1)
        if default_value:
            param.default_value = default_value
        return ordered_param

    def add_input(
        self,
        name: str,
        param_type: str,
        optional: bool = False,
        unbounded=False,
        default_value: ValueSpecification = None,
    ) -> OrderedPropertyValue:
        """Add an input Parameter for this Behavior

        Note: Current assumption is that cardinality is either [0..1] or 1

        :param name: name of the parameter, which will also be used for pins
        :param param_type: URI specifying the type of object that is expected for this parameter
        :param optional: True if the Parameter is optional; default is False
        :param default_value: default value for this parameter
        :return: Parameter that has been added
        """
        return self.add_parameter(
            name, param_type, PARAMETER_IN, optional, unbounded, default_value
        )

    def add_output(self, name, param_type) -> OrderedPropertyValue:
        """Add an output Parameter for this Behavior

        :param name: name of the parameter, which will also be used for pins
        :param param_type: URI specifying the type of object that is expected for this parameter
        :return: Parameter that has been added
        """
        return self.add_parameter(name, param_type, PARAMETER_OUT)

    def get_inputs(self) -> Iterable[Parameter]:
        """Return all Parameters of type input for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Iterator over Parameters
        """
        return (
            p for p in self.parameters if p.property_value.direction == PARAMETER_IN
        )

    def get_input(self, name) -> Parameter:
        """Return a specific input Parameter for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Parameter, or Value error
        """
        found = [p for p in self.get_inputs() if p.property_value.name == name]
        if len(found) == 0:
            raise ValueError(
                f"Behavior {self.identity} has no input parameter named {name}"
            )
        elif len(found) > 1:
            raise ValueError(
                f"Behavior {self.identity} has multiple input parameters named {name}"
            )
        else:
            return found[0]

    def get_required_inputs(self):
        """Return all required Parameters of type input for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Iterator over Parameters
        """
        # return (p for p in self.get_inputs() if p.property_value.lower_value.value > 0)
        return (
            p
            for p in self.get_inputs()
            if p.property_value.lower_value is not None
            and p.property_value.lower_value.value > 0
        )

    def get_outputs(self):
        """Return all Parameters of type output for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Iterator over Parameters
        """
        return (
            p for p in self.parameters if p.property_value.direction == PARAMETER_OUT
        )

    def get_output(self, name) -> Parameter:
        """Return a specific input Parameter for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Parameter, or Value error
        """
        found = [
            p.property_value
            for p in self.get_outputs()
            if p.property_value.name == name
        ]
        if len(found) == 0:
            raise ValueError(
                f"Behavior {self.identity} has no output parameter named {name}"
            )
        elif len(found) > 1:
            raise ValueError(
                f"Behavior {self.identity} has multiple output parameters named {name}"
            )
        else:
            return found[0]

    def get_required_outputs(self):
        """Return all required Parameters of type output for this Behavior

        Note: assumes that type is all either in or out
        Returns
        -------
        Iterator over Parameters
        """
        return (p for p in self.get_outputs() if p.property_value.lower_value.value > 0)
