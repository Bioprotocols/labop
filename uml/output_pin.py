"""
The OutputPin class defines the functions corresponding to the dynamically generated labop class OutputPin
"""

from typing import Callable, Dict, List, Union

from . import inner
from .literal_specification import LiteralSpecification
from .pin import Pin
from .utils import literal


class OutputPin(inner.OutputPin, Pin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def get_value(
        self,
        edge: "ActivityEdge",
        node_inputs: Dict[str, Union[List[LiteralSpecification], LiteralSpecification]],
        node_outputs: Callable,
        sample_format: str,
        invocation_hash: int,
    ):
        from .control_flow import ControlFlow
        from .object_flow import ObjectFlow

        value = ""
        reference = False

        if isinstance(edge, ControlFlow):
            value = ["uml.ControlFlow"]
        elif isinstance(edge, ObjectFlow):
            call_node = self.get_parent()
            # parameter = call_node.get_parameter(
            #     edge.get_source().name
            # ).property_value
            value = node_inputs[self.name]
            reference = True

        if isinstance(value, list):
            value = [literal(v, reference=reference) for v in value]
        else:
            value = [literal(value, reference=reference)]
        return value
