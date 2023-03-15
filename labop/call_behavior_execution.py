"""
The CallBehaviorExecution class defines the functions corresponding to the dynamically generated labop class CallBehaviorExecution
"""

from typing import List

import sbol3

import labop.inner as inner
from uml import PARAMETER_IN, PARAMETER_OUT, ActivityNode, Behavior, labop_hash, literal
from uml.call_behavior_action import CallBehaviorAction
from uml.literal_reference import LiteralReference

from .activity_node_execution import ActivityNodeExecution
from .behavior_execution import BehaviorExecution
from .parameter_value import ParameterValue


class CallBehaviorExecution(inner.CallBehaviorExecution, ActivityNodeExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity)

    def behavior(self):
        return self.node.lookup().behavior.lookup()

    def get_outputs(self) -> List[ParameterValue]:
        return [
            x
            for x in self.call.lookup().parameter_values
            if x.parameter.lookup().property_value.direction == PARAMETER_OUT
        ]

    def get_inputs(self) -> List[ParameterValue]:
        return [
            x
            for x in self.call.lookup().parameter_values
            if x.parameter.lookup().property_value.direction == PARAMETER_IN
        ]

    def compute_output(self, parameter, sample_format):
        """
        Get parameter value from call behavior execution
        :param self:
        :param parameter: output parameter to define value
        :return: value
        """
        node: CallBehaviorAction = self.node.lookup()
        behavior: Behavior = node.behavior.lookup()
        call: BehaviorExecution = self.call.lookup()
        # call_parameter_value_inputs: List[ParameterValue] = self.get_inputs()

        # input_parameter_values = self.input_parameter_values(
        #     inputs=call_parameter_value_inputs
        # )

        input_map = self.input_parameter_map()
        value = behavior.compute_output(input_map, parameter, sample_format, hash(self))

        return value

    # FIXME this function uses tokens, but it was previously part of uml.CallBehaviorAction, which would not have tokens.  It also only has p-v pairs as input to "inputs".
    # def input_parameter_values(self, inputs=None):
    #     """
    #     Get parameter values for all inputs
    #     :param self:
    #     :param parameter: output parameter to define value
    #     :return: value
    #     """
    #     node: CallBehaviorAction = self.node.lookup()

    #     # Get the parameter values from input tokens for input pins
    #     input_pin_values = {}
    #     # if inputs:
    #     #     input_pin_values = {
    #     #         token.lookup()
    #     #         .token_source.lookup()
    #     #         .node.lookup()
    #     #         .identity: literal(token.value, reference=True)
    #     #         for token in self.incoming_flows
    #     #         if not token.lookup().edge
    #     #     }

    #     # Get Input value pins
    #     value_pin_values = {
    #         pin.identity: pin.value
    #         for pin in node.inputs
    #         if hasattr(pin, "value")
    #     }
    #     # Convert References
    #     value_pin_values = {
    #         k: (
    #             LiteralReference(value=self.document.find(v.value))
    #             if hasattr(v, "value")
    #             and (
    #                 isinstance(v.value, sbol3.refobj_property.ReferencedURI)
    #                 or isinstance(v, LiteralReference)
    #             )
    #             else LiteralReference(value=v)
    #         )
    #         for k, v in value_pin_values.items()
    #     }
    #     # pin_values = {**input_pin_values, **value_pin_values}  # merge the dicts

    #     parameter_values = [
    #         ParameterValue(
    #             parameter=node.pin_parameter(pin.name).property_value,
    #             value=pin_values[pin.identity],
    #         )
    #         for pin in node.inputs
    #         if pin.identity in pin_values
    #     ]
    #     return parameter_values

    def input_parameter_map(
        self,
        # , inputs: List[ParameterValue] = None
    ):
        # if inputs is None:
        inputs = self.get_inputs()

        map = {input.parameter.lookup().property_value.name: [] for input in inputs}
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value.get_value()
            map[i_parameter.name].append(value)
        map = {k: (v[0] if len(v) == 1 else v) for k, v in map.items()}
        return map
