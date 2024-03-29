"""
The CallBehaviorAction class defines the functions corresponding to the
dynamically generated labop class CallBehaviorAction
"""

from typing import List

import graphviz
import sbol3

from uml.parameter import Parameter

from . import inner
from .activity_node import ActivityNode
from .activity_parameter_node import ActivityParameterNode
from .call_action import CallAction
from .control_flow import ControlFlow
from .initial_node import InitialNode
from .input_pin import InputPin
from .invocation_action import InvocationAction
from .literal_specification import LiteralSpecification
from .object_flow import ObjectFlow
from .utils import inner_to_outer, labop_hash, literal
from .value_pin import ValuePin


class CallBehaviorAction(inner.CallBehaviorAction, CallAction):
    def __init__(self, *args, **kwargs):
        super(CallBehaviorAction, self).__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity)

    def get_behavior(self):
        return self.behavior.lookup()

    def to_dot(
        self,
        dot: graphviz.Graph,
        color=None,
        incoming_edges: List["ActivityEdge"] = None,
        done=None,
        ready=None,
        namespace=None,
    ):
        from .activity import Activity

        ActivityNode.to_dot(
            self,
            dot,
            color=color,
            incoming_edges=incoming_edges,
            done=done,
            ready=ready,
            namespace=namespace,
        )
        behavior = self.get_behavior()
        subgraph = None
        if isinstance(behavior, Activity):
            subgraph = behavior.to_dot(done=done, ready=ready)
        return subgraph

    def dot_attrs(self, incoming_edges: List["ActivityEdge"]):
        port_row = '  <tr><td><table border="0" cellspacing="-2"><tr><td> </td>{}<td> </td></tr></table></td></tr>\n'
        required_inputs = self.get_behavior().get_parameters(
            required=True, input_only=True
        )
        used_inputs = [
            o
            for o in self.inputs
            if isinstance(o, ValuePin) or o in [e.get_source() for e in incoming_edges]
        ]
        unsat_inputs = [
            o for o in required_inputs if o.name not in [i.name for i in used_inputs]
        ]
        in_ports = "<td> </td>".join(
            f'<td port="{i.display_id}" border="1">{i.dot_node_name()}</td>'
            for i in used_inputs
        )
        unsat_in_ports = "<td> </td>".join(
            f'<td port="{i.display_id}" bgcolor="red" border="1">{i.label()}</td>'
            for i in unsat_inputs
        )
        in_row = (
            port_row.format(in_ports + "<td> </td>" + unsat_in_ports)
            if in_ports or unsat_in_ports
            else ""
        )
        out_ports = "<td> </td>".join(
            f'<td port="{o.display_id}" border="1">{o.name}</td>'
            for o in self.get_outputs()
        )
        out_row = port_row.format(out_ports) if out_ports else ""

        node_row = f'  <tr><td port="node" border="1">{self.behavior.lookup().display_id}</td></tr>\n'
        table_template = '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
        label = table_template.format(in_row, node_row, out_row)
        shape = "none"
        return {"label": label, "shape": shape, "style": "rounded"}

    def auto_advance(self):
        """
        Is the node executable without additional manual input?

        Returns
        -------
        bool
            Whether the node can be automatically executed.
        """
        behavior = self.get_behavior()
        return behavior.auto_advance()
