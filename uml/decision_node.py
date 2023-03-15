"""
The DecisionNode class defines the functions corresponding to the dynamically generated labop class DecisionNode
"""

import uml.inner as inner

from .control_flow import ControlFlow
from .control_node import ControlNode
from .object_flow import ObjectFlow
from .object_node import ObjectNode
from .output_pin import OutputPin
from .utils import literal


class DecisionNode(inner.DecisionNode, ControlNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dot_attrs(self):
        return {"label": "", "shape": "diamond"}

    def add_decision_output(self, protocol, guard, target):
        """Attach a guarded edge between DecisionNode and target.

        Args:
            protocol (labop.Protocol): The protocol with the self DecisionNode.
            guard (primitive type): edge guard
            target (uml.ActivityNode): edge target
        """

        kwargs = {"source": self, "target": target}
        kwargs["guard"] = literal(guard)
        outgoing_edge = (
            ObjectFlow(**kwargs)
            if isinstance(self.get_primary_incoming_flow(protocol).source, ObjectNode)
            else ControlFlow(**kwargs)
        )
        protocol.edges.append(outgoing_edge)

    def get_primary_incoming_flow(self, protocol):
        try:
            primary_incoming_flow = next(
                e
                for e in protocol.edges
                if e.target is not None
                and e.target.lookup() == self
                and e != self.decision_input_flow
                and not (
                    isinstance(e.source.lookup(), OutputPin)
                    and e.source.lookup().get_parent().behavior == self.decision_input
                )
            )
            return primary_incoming_flow
        except StopIteration as e:
            raise Exception(
                f"Could not find primary_incoming edge for DecisionNode: {self.identity}"
            )

    def get_decision_input_node(self):
        if hasattr(self, "decision_input") and self.decision_input:
            return self.decision_input
        else:
            # primary input flow leads to decision
            primary_incoming_flow = self.get_primary_incoming_flow(self.protocol())
            return primary_incoming_flow.source.lookup().get_decision_input_node()
