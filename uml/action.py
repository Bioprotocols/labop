"""
The Action class defines the functions corresponding to the dynamically generated labop class Action
"""

from typing import Callable, Dict, List

import sbol3

from . import inner
from .activity_edge import ActivityEdge
from .control_flow import ControlFlow
from .executable_node import ExecutableNode
from .literal_specification import LiteralSpecification
from .object_flow import ObjectFlow
from .utils import inner_to_outer, literal


class Action(inner.Action, ExecutableNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs

    def required_inputs(self):
        return [i for i in self.get_inputs() if i.required()]

    def required_outputs(self):
        return [o for o in self.get_outputs() if o.required()]

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

    def pin_parameter(self, pin_name: str):
        """Find the behavior parameter corresponding to the pin

        :param pin_name:
        :return: Parameter with specified name
        """
        try:
            pins = self.input_pins(pin_name)
        except:
            try:
                pin = self.output_pin(pin_name)
            except:
                raise ValueError(f"Could not find pin named {pin_name}")
        behavior = self.behavior.lookup()
        parameters = [
            p for p in behavior.parameters if p.property_value.name == pin_name
        ]
        if len(parameters) == 0:
            raise ValueError(
                f"Invalid parameter {pin_name} provided for Primitive {behavior.display_id}"
            )
        elif len(parameters) > 1:
            raise ValueError(
                f"Primitive {behavior.display_id} has multiple Parameters with the same name"
            )
        parameter = parameters[0]
        # try:
        #     parameter.__class__ = inner_to_outer(parameter)
        # except:
        #     pass
        # try:
        #     parameter.property_value.__class__ = inner_to_outer(
        #         parameter.property_value
        #     )
        # except:
        #     pass
        return parameter

    def enabled(
        self,
        edge_values: Dict[ActivityEdge, List[LiteralSpecification]],
        permissive=False,
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
        control_tokens_present = super().enabled(edge_values, permissive=permissive)

        if not permissive and control_tokens_present:
            required_inputs = self.required_inputs()
            return (
                all(
                    [
                        p.enabled(edge_values, permissive=permissive)
                        for p in required_inputs
                    ]
                )
                or permissive
            )

        else:
            return control_tokens_present

    def get_value(
        self,
        edge: ActivityEdge,
        node_inputs: Dict[ActivityEdge, LiteralSpecification],
        node_outputs: Callable,
        sample_format: str,
    ):
        value = ""
        reference = False

        if isinstance(edge, ControlFlow):
            value = "uml.ControlFlow"
        elif isinstance(edge, ObjectFlow):
            parameter = self.pin_parameter(edge.source().name).property_value
            value = self.get_parameter_value(parameter, node_outputs, sample_format)
            reference = isinstance(value, sbol3.Identified) and value.identity != None

        value = literal(value, reference=reference)
        return value
