"""
The Action class defines the functions corresponding to the dynamically generated labop class Action
"""

from typing import Dict, List

import sbol3

from uml.behavior import Behavior
from uml.input_pin import InputPin

from . import inner
from .executable_node import ExecutableNode
from .literal_specification import LiteralSpecification
from .output_pin import OutputPin
from .parameter import Parameter
from .pin import Pin
from .utils import WellFormednessError, WellFormednessIssue
from .value_pin import ValuePin


class Action(inner.Action, ExecutableNode):
    def __init__(self, *args, **kwargs):
        super(Action, self).__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def initialize_parameter_maps(self):
        self.pin_parameters = {}
        self.pin_ordered_parameters = {}
        behavior = self.get_behavior()
        # parameters = behavior.get_parameters()
        ordered_parameters = list(behavior.get_parameters(ordered=True))
        for i in self.inputs:
            if i.name not in self.pin_parameters:
                self.pin_parameters[i.name] = []
            if i.name not in self.pin_ordered_parameters:
                self.pin_ordered_parameters[i.name] = []

            self.pin_ordered_parameters[i.name] += [
                p
                for p in ordered_parameters
                if p.property_value.name == i.name and p.property_value.is_input()
            ]
            self.pin_parameters[i.name] += [
                p.property_value
                for p in ordered_parameters
                if p.property_value.name == i.name and p.property_value.is_input()
            ]

        for o in self.outputs:
            if o.name not in self.pin_parameters:
                self.pin_parameters[o.name] = []
            if o.name not in self.pin_ordered_parameters:
                self.pin_ordered_parameters[o.name] = []

            self.pin_parameters[o.name] += [
                p.property_value
                for p in ordered_parameters
                if p.property_value.name == o.name and p.property_value.is_output()
            ]
            self.pin_ordered_parameters[o.name] += [
                p
                for p in ordered_parameters
                if p.property_value.name == o.name and p.property_value.is_output()
            ]

        self.pin_parameters = {k: list(set(v)) for k, v in self.pin_parameters.items()}
        self.pin_ordered_parameters = {
            k: list(set(v)) for k, v in self.pin_ordered_parameters.items()
        }

    def get_inputs(self) -> List[InputPin]:
        return self.inputs

    def get_outputs(self) -> List[OutputPin]:
        return self.outputs

    def get_pins(self) -> List[Pin]:
        return self.inputs + self.outputs

    def required_inputs(self) -> List[InputPin]:
        return [
            i for i in self.get_inputs() if self.get_parameter(name=i.name).required()
        ]

    def required_outputs(self) -> List[OutputPin]:
        return [
            o for o in self.get_outputs() if self.get_parameter(name=o.name).required()
        ]

    def input_pin(self, pin_name: str):
        """Find an input pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.get_inputs() if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(
                f"Could not find input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        if len(pin_set) > 1:
            raise ValueError(
                f"Found more than one input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        return pin_set.pop()

    def input_pins(self, pin_name: str):
        """Find an input pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.get_inputs() if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(
                f"Could not find input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        return pin_set

    def output_pin(self, pin_name: str):
        """Find an output pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.get_outputs() if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(f"Could not find output pin named {pin_name}")
        if len(pin_set) > 1:
            raise ValueError(f"Found more than one output pin named {pin_name}")
        return pin_set.pop()

    def get_behavior(self) -> Behavior:
        return self.behavior.lookup()

    def get_parameter(self, name: str = None, ordered=False):
        """Find the behavior parameter corresponding to the pin with the name

        :param pin_name:
        :return: Parameter with specified name
        """
        if name is None:
            return None
        if not hasattr(self, "pin_ordered_parameters"):
            self.initialize_parameter_maps()
        if name in self.pin_ordered_parameters:
            params = (
                self.pin_ordered_parameters[name]
                if ordered
                else self.pin_parameters[name]
            )
            if len(params) > 1:
                raise ValueError(
                    f"Primitive {behavior.display_id} has multiple Parameters with the same name"
                )
            elif len(params) == 0:
                raise ValueError(
                    f"The pin with name {name} exists, but does not match a parameter for Primitive {self.get_behavior().display_id}"
                )
            return next(iter(params))
        else:
            raise ValueError(
                f"Invalid parameter {name} provided for Primitive {self.get_behavior().display_id}"
            )

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A CallBehaviorAction is well formed if:
        - the behavior is well formed
        - there is exactly one pin per required parameter
        - required parameters either have a default value or either correspond to a ValuePin with a value or an InputPin with an incoming edge
        - each pin is well formed
        """
        pins: List[Pin] = []
        pins += self.get_inputs()
        pins += self.get_outputs()
        behavior: Behavior = self.get_behavior()

        issues = []

        issues += behavior.is_well_formed()

        required_parameters: List[Parameter] = []
        required_parameters += behavior.get_parameters(ordered=False, required=True)

        all_parameters = behavior.get_parameters(ordered=False)

        for pin in pins:
            matching_parameter = None
            for param in all_parameters:
                if pin.name == param.name and (
                    (param.is_input() and isinstance(pin, InputPin))
                    or (param.is_output() and isinstance(pin, OutputPin))
                ):
                    matching_parameter = param
                    break
            if matching_parameter is None:
                issues += [
                    WellFormednessError(
                        self,
                        f"Action has a pin {pin.name} that does not correspond to a parameter.",
                    )
                ]

        for param in required_parameters:
            matching_pin = None
            for pin in pins:
                if pin.name == param.name and (
                    (param.is_input() and isinstance(pin, InputPin))
                    or (param.is_output() and isinstance(pin, OutputPin))
                ):
                    matching_pin = pin
                    break
            if matching_pin is None:
                issues += [
                    WellFormednessError(
                        self,
                        f"Action does not have a pin for required parameter {param}.",
                    )
                ]
            else:
                issues += matching_pin.is_well_formed()

        return issues

    def enabled(
        self,
        edge_values: Dict["ActivityEdge", List[LiteralSpecification]],
        engine: "ExecutionEngine",
    ):
        """Check whether all incoming edges have values defined by a token in tokens and that all value pin values are
        defined.

        Parameters
        ----------
        self: node to be executed
        edge_values: current list of pending edge flows

        Returns
        -------
        bool if self is enabled
        """

        # Need all incoming control tokens
        control_tokens_present = super().enabled(edge_values, engine)

        if not engine.permissive and control_tokens_present:
            required_inputs = self.required_inputs()
            required_value_pins = [
                p for p in required_inputs if isinstance(p, ValuePin)
            ]
            required_input_pins = [
                p for p in required_inputs if p not in required_value_pins
            ]
            return (
                # ValuePin will not produce a token, so check if enabled
                all([p.enabled(None, engine) for p in required_value_pins])
                and
                # InputPin will have a token on the edge
                all(
                    [
                        len(edge_values[e]) > 0
                        for p in required_input_pins
                        for e in edge_values
                        if e.get_source() == p
                    ]
                )
            ) or engine.permissive

        else:
            return control_tokens_present
