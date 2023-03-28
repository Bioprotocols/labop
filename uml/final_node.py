"""
The FinalNode class defines the functions corresponding to the dynamically generated labop class FinalNode
"""

from typing import Callable, List

import uml
from uml.activity_edge import ActivityEdge

from . import inner
from .control_node import ControlNode


class FinalNode(inner.FinalNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {
            "label": "",
            "shape": "doublecircle",
            "style": "filled",
            "fillcolor": "black",
        }

    def enabled(
        self,
        engine: "ExecutionEngine",
        tokens: List["ActivityEdgeFlow"],
    ):
        """
        Check whether there exists at least one token on an incoming edge.

        Parameters
        ----------
        self
            Node to execute
        engine : "ExecutionEngine"
            the engine executing the node
        tokens : List["ActivityEdgeFlow"]
            tokens offered to node

        Returns
        -------
        bool
            is the node enabled
        """
        protocol = self.protocol()
        token_present = (
            len(
                {t.edge.lookup() for t in tokens if t.edge}.intersection(
                    protocol.incoming_edges(self)
                )
            )
            > 0
        )
        return token_present

    def next_tokens_callback(
        self,
        source: "ActivityNodeExecution",
        engine: "ExecutionEngine",
        out_edges: List[ActivityEdge],
        node_outputs: Callable,
    ) -> List["ActivityEdgeFlow"]:
        calling_behavior_execution = source.get_calling_behavior_execution()
        if calling_behavior_execution:
            new_tokens = calling_behavior_execution.complete_subprotocol(engine)
            return new_tokens
        else:
            return []
