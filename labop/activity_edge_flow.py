"""
The ActivityEdgeFlow class defines the functions corresponding to the dynamically generated labop class ActivityEdgeFlow
"""

import labop
import labop.inner as inner
from uml import CallBehaviorAction, InputPin, Parameter

from .protocol import Protocol


class ActivityEdgeFlow(inner.ActivityEdgeFlow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_target(self):
        """Find the target node of an edge flow
        Parameters
        ----------
        self

        Returns ActivityNode
        -------

        """
        token_source_node = self.token_source.lookup().node.lookup()
        if self.edge:
            target = self.edge.lookup().target.lookup()
        elif isinstance(
            token_source_node, InputPin
        ):  # Tokens for pins do not have an edge connecting pin to activity
            target = token_source_node.get_parent()
        elif isinstance(token_source_node, CallBehaviorAction) and isinstance(
            token_source_node.behavior.lookup(), Protocol
        ):
            # If no edge (because cannot link to InitialNode), then if source is calling a subprotocol, use subprotocol initial node
            target = token_source_node.behavior.lookup().initial()
        else:
            raise Exception(f"Cannot find the target node of edge flow: {self}")
        return target

    def info(self):
        return {
            "edge_type": (type(self.edge.lookup()) if self.edge else None),
            "source": self.token_source.lookup().node.lookup().identity,
            "target": self.get_target().identity,
            "behavior": (
                self.get_target().behavior
                if isinstance(self.get_target(), CallBehaviorAction)
                else None
            ),
        }

    def get_token_source(
        self,
        parameter: Parameter,
        target: labop.ActivityNodeExecution = None,
    ) -> labop.CallBehaviorExecution:
        node = self.token_source.lookup().node.lookup()
        print(self.identity + " src = " + node.identity + " param = " + str(parameter))
        if parameter and isinstance(node, InputPin):
            if node == target.node.lookup().input_pin(parameter.name):
                return self.token_source.lookup().get_token_source(None, target=target)
            else:
                return None
        elif not parameter:
            return self.token_source.lookup().get_token_source(None, target=target)
        else:
            return None
