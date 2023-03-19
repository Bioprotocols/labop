"""
The CallBehaviorAction class defines the functions corresponding to the dynamically generated labop class CallBehaviorAction
"""

import uuid
from typing import Callable, Dict, List

from uml.invocation_action import InvocationAction
from uml.literal_specification import LiteralSpecification

from . import inner
from .activity_edge import ActivityEdge
from .activity_node import ActivityNode
from .activity_parameter_node import ActivityParameterNode
from .call_action import CallAction
from .control_flow import ControlFlow
from .initial_node import InitialNode
from .object_flow import ObjectFlow
from .utils import inner_to_outer, literal
from .value_pin import ValuePin


class CallBehaviorAction(inner.CallBehaviorAction, CallAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def behavior(self):
        return self.behavior.lookup()

    def dot_attrs(self):
        port_row = '  <tr><td><table border="0" cellspacing="-2"><tr><td> </td>{}<td> </td></tr></table></td></tr>\n'
        in_ports = "<td> </td>".join(
            f'<td port="{i.display_id}" border="1">{i.dot_node_name()}</td>'
            for i in self.inputs
        )
        in_row = port_row.format(in_ports) if in_ports else ""
        out_ports = "<td> </td>".join(
            f'<td port="{o.display_id}" border="1">{o.name}</td>' for o in self.outputs
        )
        out_row = port_row.format(out_ports) if out_ports else ""

        node_row = f'  <tr><td port="node" border="1">{self.behavior.lookup().display_id}</td></tr>\n'
        table_template = '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
        label = table_template.format(in_row, node_row, out_row)
        shape = "none"
        return {"label": label, "shape": shape, "style": "rounded"}

    def next_tokens_callback(
        self,
        node_inputs: Dict[ActivityEdge, LiteralSpecification],
        outgoing_edges: List[ActivityEdge],
        node_outputs: Callable,
        calling_behavior: InvocationAction,
        sample_format: str,
        permissive: bool,
    ) -> Dict[ActivityEdge, LiteralSpecification]:
        if isinstance(self.behavior(), Activity):
            if engine.is_asynchronous:
                # Push record onto blocked nodes to complete
                engine.blocked_nodes.add(source)
                # new_tokens are those corresponding to the subprotocol initiating_nodes
                init_nodes = self.behavior.lookup().initiating_nodes()

                def get_invocation_edge(r, n):
                    invocation = {}
                    value = None
                    if isinstance(n, InitialNode):
                        try:
                            invocation["edge"] = ControlFlow(source=r.node, target=n)
                            engine.ex.activity_call_edge += [invocation["edge"]]
                            source = next(
                                i
                                for i in r.incoming_flows
                                if hasattr(i.lookup(), "edge")
                                and i.lookup().edge
                                and isinstance(i.lookup().edge.lookup(), ControlFlow)
                            )
                            invocation["value"] = literal(
                                source.lookup().value, reference=True
                            )

                        except StopIteration as e:
                            pass

                    elif isinstance(n, ActivityParameterNode):
                        # if ActivityParameterNode is a ValuePin of the calling behavior, then it won't be an incoming flow
                        source = self.input_pin(
                            n.parameter.lookup().property_value.name
                        )
                        invocation["edge"] = ObjectFlow(source=source, target=n)
                        engine.ex.activity_call_edge += [invocation["edge"]]
                        # ex.protocol.lookup().edges.append(invocation['edge'])
                        if isinstance(source, ValuePin):
                            invocation["value"] = literal(source.value, reference=True)
                        else:
                            try:
                                source = next(
                                    iter(
                                        [
                                            i
                                            for i in r.incoming_flows
                                            if i.lookup()
                                            .token_source.lookup()
                                            .node.lookup()
                                            .name
                                            == n.parameter.lookup().property_value.name
                                        ]
                                    )
                                )
                                # invocation['edge'] = ObjectFlow(source=source.lookup().token_source.lookup().node.lookup(), target=n)
                                # engine.ex.activity_call_edge += [invocation['edge']]
                                # ex.protocol.lookup().edges.append(invocation['edge'])
                                invocation["value"] = literal(
                                    source.lookup().value, reference=True
                                )
                            except StopIteration as e:
                                pass

                    return invocation

                new_tokens = {
                    source: get_invocation_edge(source, init_node)
                    for init_node in init_nodes
                }
                # engine.ex.flows += new_tokens

                if len(new_tokens) == 0:
                    # Subprotocol does not have a body, so need to complete the CallBehaviorAction here, otherwise would have seen a FinalNode.
                    new_tokens = source.complete_subprotocol(engine)

            else:  # is synchronous execution
                # Execute subprotocol
                self.execute(
                    self.behavior.lookup(),
                    engine.ex.association[0].agent.lookup(),
                    id=f"{engine.display_id}{uuid.uuid4()}".replace("-", "_"),
                    parameter_values=[],
                )
        else:
            new_tokens = self.next_tokens_callback(
                source, engine, out_edges, node_outputs
            )

        return new_tokens
