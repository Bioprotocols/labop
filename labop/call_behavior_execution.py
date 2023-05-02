"""
The CallBehaviorExecution class defines the functions corresponding to the dynamically generated labop class CallBehaviorExecution
"""

from typing import Callable, List, Union

from labop import inner
from uml import (
    PARAMETER_IN,
    PARAMETER_OUT,
    Action,
    ActivityParameterNode,
    Behavior,
    CallBehaviorAction,
    ObjectFlow,
    Parameter,
    labop_hash,
    literal,
)
from uml.ordered_property_value import OrderedPropertyValue
from uml.output_pin import OutputPin

from .activity_edge_flow import ActivityEdgeFlow
from .activity_node_execution import ActivityNodeExecution
from .behavior_execution import BehaviorExecution
from .parameter_value import ParameterValue


class CallBehaviorExecution(inner.CallBehaviorExecution, ActivityNodeExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return (
            labop_hash(self.identity)
            + hash(self.get_node())
            + sum([hash(pv) for pv in self.parameter_values()])
        )

    def get_behavior(self) -> Behavior:
        return self.get_node().get_behavior()

    def get_node(self) -> Action:
        return self.node.lookup()

    def get_call(self) -> BehaviorExecution:
        return self.call.lookup()

    def parameter_values(self) -> List[ParameterValue]:
        return self.get_call().parameter_values

    def parameter_value_map(self):
        return self.get_call().parameter_value_map()

    def get_parameter(self, name: str):
        return self.get_node().get_parameter(name)

    def get_outputs(self) -> List[ParameterValue]:
        return [
            x
            for x in self.get_call().parameter_values
            if x.parameter.lookup().property_value.direction == PARAMETER_OUT
        ]

    def get_inputs(self) -> List[ParameterValue]:
        return [
            x
            for x in self.get_call().parameter_values
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
        behavior: Behavior = self.get_behavior()
        call: BehaviorExecution = self.get_call()
        # call_parameter_value_inputs: List[ParameterValue] = self.get_inputs()

        # input_parameter_values = self.input_parameter_values(
        #     inputs=call_parameter_value_inputs
        # )

        input_map = self.input_parameter_map()
        value = behavior.compute_output(input_map, parameter, sample_format, hash(self))

        return value

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

    def get_parameter(
        self, pin_name: str, ordered=False
    ) -> Union[OrderedPropertyValue, Parameter]:
        return self.get_node().get_parameter(pin_name, ordered=ordered)

    def check_next_tokens(
        self,
        tokens: List[ActivityEdgeFlow],
        node_outputs: Callable,
        perimssive: bool,
        sample_format: str,
    ):
        call = self.get_call()
        behavior: Behavior = self.get_behavior()
        # ## Add the output values to the call parameter-values
        for token in tokens:
            edge = token.get_edge()
            if isinstance(edge, ObjectFlow):
                target: OutputPin = edge.get_target()  # target is an OutputPin
                call.parameter_values += [
                    ParameterValue(
                        parameter=self.get_parameter(target.name, ordered=True),
                        value=literal(token.value.get_value(), reference=True),
                    )
                ]

        ### Check that the same parameter names are sane:
        # 1. unbounded parameters can appear 0+ times
        # 2. unique parameters must not have duplicate values (unbounded, unique means no pair of values is the same)
        # 3. required parameters are present

        pin_sets = {}
        for pv in call.parameter_values:
            name = pv.get_parameter().name
            value = pv.value.get_value() if pv.value else None
            if name not in pin_sets:
                pin_sets[name] = []
            pin_sets[name].append(value)

        parameter_value_map = call.parameter_value_map()

        for p, v in parameter_value_map.items():
            param = self.get_parameter(p)

            if (
                param.lower_value
                and param.lower_value.value > 0
                and param.name not in pin_sets
            ):
                raise ValueError(
                    f"Parameter '{param.name}' is required, but does not appear as a pin"
                )

            elif param.name in pin_sets:
                count = len(pin_sets[param.name])
                unique_count = len(set(pin_sets[param.name]))
                if param.is_unique:
                    if count != unique_count:
                        raise ValueError(
                            f"{param.name} has {count} values, but only {unique_count} are unique"
                        )
                if (param.lower_value and param.lower_value.value > count) or (
                    param.upper_value and param.upper_value.value < count
                ):
                    raise ValueError(
                        f"{param.name} has {count} values, but expecting [{param.lower_value.value}, {param.upper_value.value}] values"
                    )

    def get_token_source(
        self,
        parameter: Parameter,
        target: ActivityNodeExecution = None,
    ):
        node = self.node.lookup()
        print(self.identity + " " + node.identity + " param = " + str(parameter))
        if parameter:
            return ActivityNodeExecution.get_token_source(
                self, parameter, target=target
            )
        else:
            return self
