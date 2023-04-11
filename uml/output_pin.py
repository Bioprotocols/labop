"""
The OutputPin class defines the functions corresponding to the dynamically generated labop class OutputPin
"""

from typing import Callable, Dict, List, Union

from . import inner
from .control_flow import ControlFlow
from .literal_specification import LiteralSpecification
from .object_flow import ObjectFlow
from .pin import Pin
from .utils import literal


class OutputPin(inner.OutputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_decision_input_node(self):
        return self.get_parent()

    def get_value(
        self,
        edge: "ActivityEdge",
        node_inputs: Dict[str, Union[List[LiteralSpecification], LiteralSpecification]],
        node_outputs: Callable,
        sample_format: str,
        invocation_hash: int,
    ):
        value = ""
        reference = False

        if isinstance(edge, ControlFlow):
            value = "uml.ControlFlow"
        elif isinstance(edge, ObjectFlow):
            call_node = self.get_parent()
            # parameter = call_node.pin_parameter(
            #     edge.get_source().name
            # ).property_value
            value = node_inputs[self.name]
            reference = True

        value = literal(value, reference=reference)
        return value
