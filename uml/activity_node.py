"""
The ActivityNode class defines the functions corresponding to the dynamically generated labop class ActivityNode
"""

import logging
from typing import Callable, Dict, List

from . import inner
from .activity_edge import ActivityEdge
from .control_flow import ControlFlow
from .literal_specification import LiteralSpecification
from .object_flow import ObjectFlow
from .parameter import Parameter
from .utils import labop_hash, literal

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class ActivityNode(inner.ActivityNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity)

    def required(self):
        return (
            hasattr(self, "lower_value")
            and self.lower_value is not None
            and self.lower_value.value > 0
        )

    def unpin(self):
        """Find the root node for an ActivityNode: either itself if a Pin, otherwise the owning Action

        Parameters
        ----------
        self: ActivityNode

        Returns
        -------
        self if not a Pin, otherwise the owning Action
        """
        return self

    def dot_attrs(self):
        return {"label": "", "shape": "circle"}

    def enabled(
        self,
        edge_values: Dict[ActivityEdge, List[LiteralSpecification]],
        permissive=False,
    ):
        incoming_controls = {e for e in edge_values if isinstance(e, ControlFlow)}
        if len(incoming_controls) > 0:
            # Need all incoming control tokens
            control_tokens_present = all(
                [len(edge_values[ic]) > 0 for ic in incoming_controls]
            )
            return control_tokens_present
        else:
            return False  # Cannot execute a node with no incoming controls unless its an InitialNode

    # def execute(
    #     self,
    #     edge_values: Dict[ActivityEdge, List[LiteralSpecification]],
    #     outgoing_edges: List[ActivityEdge],
    #     node_outputs: Callable,
    #     calling_behavior: InvocationAction,
    #     sample_format: str,
    #     permissive: bool,
    # ) -> Tuple[
    #     Dict[ActivityEdge, List[LiteralSpecification]],  # consumed values for record
    #     Dict[ActivityEdge, LiteralSpecification],  # produced values for tokens
    # ]:
    #     """Execute a node in an activity, consuming the incoming flows and recording execution and outgoing flows

    #     Parameters
    #     ----------
    #     self: node to be executed

    #     Returns
    #     -------
    #     updated list of pending edge flows
    #     """
    #     # Extract the relevant set of incoming flow values

    #     node_inputs = self.consume_tokens(edge_values)
    #     new_tokens: Dict[ActivityEdge, LiteralSpecification] = self.next_tokens(
    #         node_inputs,
    #         outgoing_edges,
    #         node_outputs,
    #         calling_behavior,
    #         sample_format,
    #         permissive,
    #     )

    #     # return updated token list
    #     return new_tokens, node_inputs

    # def next_tokens(
    #     self,
    #     node_inputs: Dict[ActivityEdge, List[LiteralSpecification]],
    #     outgoing_edges: List[ActivityEdge],
    #     node_outputs: Callable,
    #     calling_behavior: InvocationAction,
    #     sample_format: str,
    #     permissive: bool,
    # ) -> Dict[ActivityEdge, LiteralSpecification]:
    #     edge_tokens = self.next_tokens_callback(
    #         node_inputs,
    #         outgoing_edges,
    #         node_outputs,
    #         calling_behavior,
    #         sample_format,
    #     )
    #     self.check_next_tokens(edge_tokens, node_outputs, sample_format, permissive)

    #     return edge_tokens

    def consume_tokens(
        self, edge_values: Dict[ActivityEdge, List[LiteralSpecification]]
    ) -> Dict[ActivityEdge, List[LiteralSpecification]]:
        consumed_tokens = {
            e: next(vals) for e, vals in edge_values.items() if len(vals) > 0
        }
        return consumed_tokens

    def next_tokens_callback(
        self,
        node_inputs: Dict[ActivityEdge, LiteralSpecification],
        outgoing_edges: List[ActivityEdge],
        node_outputs: Callable,
        calling_behavior: "InvocationAction",
        sample_format: str,
        permissive: bool,
    ) -> Dict[ActivityEdge, LiteralSpecification]:
        edge_tokens = {}
        for edge in outgoing_edges:
            try:
                edge_value = self.get_value(
                    edge, node_inputs, node_outputs, sample_format
                )
            except Exception as e:
                if permissive:
                    edge_value = literal(str(e))
                else:
                    raise e

            edge_tokens[edge] = edge_value
        return edge_tokens

    def get_value(
        self,
        edge: ActivityEdge,
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
            raise Exception("ActivityNode cannot get_value of outgoing ObjectFlow")

        value = literal(value, reference=reference)
        return value
