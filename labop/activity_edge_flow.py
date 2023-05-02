"""
The ActivityEdgeFlow class defines the functions corresponding to the dynamically generated labop class ActivityEdgeFlow
"""


import graphviz
import sbol3

from labop import inner
from labop.activity_node_execution import ActivityNodeExecution
from uml import CallBehaviorAction, InputPin, LiteralReference, Parameter

from .protocol import Protocol


class ActivityEdgeFlow(inner.ActivityEdgeFlow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_edge(self):
        return self.edge.lookup()

    def get_value(self):
        return self.value

    def get_source(self):
        return self.token_source.lookup()

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
        target: "ActivityNodeExecution" = None,
    ) -> "CallBehaviorExecution":
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

    def to_dot(
        self,
        dot: graphviz.Graph,
        target_node_execution: ActivityNodeExecution,
        namespace,
        dest_parameter=None,
        out_dir=".",
        color="orange",
        reverse=False,
    ):
        source_node_execution = self.get_source()
        source_node = self.get_edge().get_source()
        edge_value = self.get_value().get_value()
        is_ref = isinstance(self.get_value(), LiteralReference)

        source_id = source_node.dot_label(namespace=namespace)
        if isinstance(source_node, CallBehaviorAction):
            source_id = f"{source_id}:node"
        target_id = target_node_execution.dot_label(namespace=namespace)
        if isinstance(target_node_execution, CallBehaviorAction):
            target_id = f"{target_id}:node"

        if isinstance(edge_value, sbol3.Identified):
            edge_label = edge_value.display_id  # value.identity
        else:
            edge_label = f"{edge_value}"

        if hasattr(edge_value, "to_dot") and not is_ref:
            # Make node for value and connect to source
            value_node_id = edge_value.to_dot(dot, out_dir=out_dir)
            dot.edge(source_id, value_node_id)

        edge_index = self.identity.split("ActivityEdgeFlow")[-1]

        edge_label = f"{edge_index}: {edge_label}"

        attrs = {"color": color}
        if reverse:
            dot.edge(source_id, target_id, edge_label, _attributes=attrs)
        else:
            dot.edge(target_id, source_id, edge_label, _attributes=attrs)
