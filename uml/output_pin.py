"""
The OutputPin class defines the functions corresponding to the dynamically generated labop class OutputPin
"""

from typing import List

from uml.control_flow import ControlFlow
from uml.object_flow import ObjectFlow

from . import inner
from .pin import Pin


class OutputPin(inner.OutputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_decision_input_node(self):
        return self.get_parent()

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
    ):
        return False

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
            call_node = self.get_parent()
            parameter = call_node.pin_parameter(edge.source().name).property_value
            value = node_inputs[edge]
            reference = True

        value = literal(value, reference=reference)
        return value
