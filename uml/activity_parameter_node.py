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

    def dot_attrs(self, incoming_edges: Dict["InputPin", List["ActivityEdge"]] = None):
        label = self.parameter.lookup().name
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

    # def get_value(self) -> Dict[Parameter, LiteralSpecification]:
    #     values = [
    #         i.value.get_value()
    #         for i in self.incoming_flows
    #         if isinstance(i.edge.lookup(), ObjectFlow)
    #     ]
    #     assert len(values) < 2, "ActivityParameterNode has too many incoming values"
    #     if len(values) == 1:
    #         return values[0]
    #     else:
    #         return None

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

    def get_value(
        self,
        edge: "ActivityEdge",
        parameter_value_map: Dict[str, List[LiteralSpecification]],
        node_outputs: Callable,
        sample_format: str,
        invocation_hash: int,
    ):
        value = ""
        reference = False

        if isinstance(edge, ControlFlow):
            value = "uml.ControlFlow"
        elif isinstance(edge, ObjectFlow):
            if self.is_output():
                value = parameter_value_map[self.name]
                reference = True

        value = literal(value, reference=reference)
        return value
