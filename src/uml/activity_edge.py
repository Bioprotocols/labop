"""
The ActivityEdge class defines the functions corresponding to the dynamically generated labop class ActivityEdge
"""

import html
from typing import List

import graphviz

from uml.activity_node import ActivityNode

from . import inner
from .action import Action
from .input_pin import InputPin
from .literal_null import LiteralNull
from .output_pin import OutputPin
from .pin import Pin
from .utils import WellFormednessIssue, WhereDefinedMixin


class ActivityEdge(inner.ActivityEdge, WhereDefinedMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._where_defined = self.get_where_defined()

    def get_source(self) -> ActivityNode:
        return self.source.lookup() if self.source else self.source

    def get_target(self) -> ActivityNode:
        return self.target.lookup() if self.target else self.target

    def gv_sanitize(self, id: str):
        return html.escape(id.replace(":", "_"))

    def label(self, namespace=None):
        if namespace:
            truncated = self.gv_sanitize(self.identity.replace(f"{self.namespace}", ""))
        else:
            truncated = self.gv_sanitize(self.identity)
        in_struct = "_".join(truncated.split("/", 1)).replace(
            "/", ":"
        )  # Replace last "/" with "_"
        return (
            in_struct  # _gv_sanitize(object.identity.replace(f'{self.identity}/', ''))
        )

    def dot_plottable(self):
        source = self.get_source()
        target = self.get_target()
        # do not plot pin to cba or cba to pin
        return not (
            (isinstance(source, InputPin) and isinstance(target, Action))
            or (isinstance(source, Action) and isinstance(target, OutputPin))
        )

    def to_dot(self, dot: graphviz.Graph, namespace=""):
        from .call_behavior_action import CallBehaviorAction
        from .decision_node import DecisionNode

        source = self.get_source()
        target = self.get_target()
        src_id = source.label(namespace=namespace)
        dest_id = target.label(namespace=namespace)
        edge_id = self.label()  # edge.identity.replace(":", "_")
        if isinstance(target, CallBehaviorAction):
            dest_id = f"{dest_id}:node"
        if isinstance(source, CallBehaviorAction):
            src_id = f"{src_id}:node"

        if isinstance(source, Pin):
            try:
                src_activity = source.get_parent()
            except Exception as e:
                print(f"Cannot find source activity for {source.identity}")

        if isinstance(target, Pin):
            try:
                dest_activity = target.get_parent()
            except Exception as e:
                print(f"Cannot find source activity for {source.identity}")

        attrs = self.dot_attrs()

        dot.edge(src_id, dest_id, **attrs)

    def dot_color(self):
        return "black"

    def dot_attrs(self):
        from .decision_node import DecisionNode

        source = self.get_source()
        if isinstance(source, DecisionNode) and hasattr(self, "guard"):
            label = (
                self.guard.value
                if self.guard
                and not isinstance(self.guard, LiteralNull)
                and self.guard.value is not None
                else "None"
            )
            label = (
                "Else" if label == "http://bioprotocols.org/uml#else" else str(label)
            )
        else:
            label = ""
        return {"color": self.dot_color(), "label": label}

    def is_well_formed(self) -> List[WellFormednessIssue]:
        return []
