"""
The ActivityParameterNode class defines the functions corresponding to the dynamically generated labop class ActivityParameterNode
"""

from typing import Callable, Dict, List

from . import inner
from .control_flow import ControlFlow
from .invocation_action import InvocationAction
from .literal_specification import LiteralSpecification
from .object_flow import ObjectFlow
from .object_node import ObjectNode
from .parameter import Parameter
from .utils import literal


class ActivityParameterNode(inner.ActivityParameterNode, ObjectNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.name = self.parameter.name
        self._where_defined = self.get_where_defined()

    def dot_attrs(self, incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None):
        label = self.get_parameter().name
        return {"label": label, "shape": "rectangle", "peripheries": "2"}

    def get_parameter(self, ordered=False):
        if ordered:
            return self.parameter.lookup()
        else:
            return self.parameter.lookup().property_value

    def is_output(self):
        return self.get_parameter().is_output()

    def is_input(self):
        return self.get_parameter().is_input()

    def next_tokens_callback(
        self,
        node_inputs: Dict["ActivityEdge", LiteralSpecification],
        outgoing_edges: List["ActivityEdge"],
        node_outputs: Callable,
        calling_behavior: InvocationAction,
        sample_format: str,
        permissive: bool,
    ) -> Dict["ActivityEdge", LiteralSpecification]:
        from .activity_edge import ActivityEdge

        if self.get_parameter().get_input():
            try:
                parameter_value = next(
                    node_inputs[self][edge]
                    for edge in node_inputs[
                        self
                    ]  # edge may be a dummy edge that is atually a ParameterValue
                    if (
                        isinstance(edge, Parameter)
                        and edge.get_parameter() == self.get_parameter()
                    )
                    or (isinstance(edge, ActivityEdge))
                )
            except StopIteration as e:
                try:
                    parameter_value = self.get_parameter().default_value
                except Exception as e:
                    raise Exception(
                        f"ERROR: Could not find input parameter {self.get_parameter().name} value and/or no default_value."
                    )
            edge_tokens = {
                edge: literal(value=parameter_value, reference=True)
                for edge in outgoing_edges
            }
        else:
            # If this is an output that is returned to a calling Activity, then make a call return edge

            if calling_behavior:
                return_edge = ObjectFlow(
                    source=self,
                    target=calling_behavior.output_pin(self.get_parameter().name),
                )

                edge_tokens = {
                    return_edge: source.get_value(
                        return_edge, node_outputs, engine.sample_format
                    )
                }

            else:
                edge_tokens = []
        return edge_tokens
