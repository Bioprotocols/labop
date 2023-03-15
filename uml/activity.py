"""
The Activity class defines the functions corresponding to the dynamically generated labop class Activity
"""

import html
import logging
from collections import Counter
from typing import Dict, Iterable, List, Set

import graphviz
import sbol3
import tyto

import uml.inner as inner
from uml.call_behavior_action import CallBehaviorAction
from uml.executable_node import ExecutableNode
from uml.join_node import JoinNode
from uml.literal_null import LiteralNull
from uml.merge_node import MergeNode
from uml.object_node import ObjectNode
from uml.output_pin import OutputPin
from uml.pin import Pin

from .activity_edge import ActivityEdge
from .activity_node import ActivityNode
from .activity_parameter_node import ActivityParameterNode
from .behavior import Behavior
from .control_flow import ControlFlow
from .decision_node import DecisionNode
from .final_node import FinalNode
from .fork_node import ForkNode
from .initial_node import InitialNode
from .input_pin import InputPin
from .literal_reference import LiteralReference
from .object_flow import ObjectFlow
from .parameter import Parameter
from .strings import PARAMETER_IN
from .utils import id_sort, literal
from .value_pin import ValuePin
from .value_specification import ValueSpecification

l = logging.Logger(__file__)
l.setLevel(logging.INFO)


class Activity(inner.Activity, Behavior):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initial(self):
        """Find or create an initial node in an Activity.

        Note that while UML allows multiple initial nodes, use of this routine assumes a single one is sufficient.
        :return: InitialNode for Activity
        """

        initial = [a for a in self.nodes if isinstance(a, InitialNode)]
        if not initial:
            self.nodes.append(InitialNode())
            return self.initial()
        elif len(initial) == 1:
            return initial[0]
        else:
            raise ValueError(
                f'Activity "{self.display_id}" assumed to have one initial node, but found {len(initial)}'
            )

    def final(self):
        """Find or create a final node in a Activity

        Note that while UML allows multiple final nodes, use of this routine assumes a single is sufficient.
        :return: FinalNode for Activity
        """
        final = [a for a in self.nodes if isinstance(a, FinalNode)]
        if not final:
            self.nodes.append(FinalNode())
            return self.final()
        elif len(final) == 1:
            return final[0]
        else:
            raise ValueError(
                f'Activity "{self.display_id}" assumed to have one initial node, but found {len(final)}'
            )

    def input_value(
        self,
        name: str,
        param_type: str,
        optional: bool = False,
        default_value: ValueSpecification = None,
    ) -> ActivityParameterNode:
        """Add an input, then return the ActivityParameterNode that refers to that input

        :param self: Activity
        :param name: Name of the input
        :param param_type: type of value expected for the input
        :param optional: True if the Parameter is optional; default is False
        :param default_value: if the input is optional, a default value must be set
        :return: ActivityParameterNode associated with the input
        """
        parameter = self.add_input(
            name=name,
            param_type=param_type,
            optional=optional,
            default_value=default_value,
        )
        node = ActivityParameterNode(parameter=parameter)
        self.nodes.append(node)
        return node

    def designate_output(
        self, name: str, param_type: str, source: ActivityNode
    ) -> ActivityParameterNode:
        """Add an output, connect it to an ActivityParameterNode, and get its value from the designated node

        :param self: Activity
        :param name: Name of the output
        :param param_type: type of value expected for the output
        :param source: ActivityNode whose ObjectValue output should be routed to the source
        :return: ActivityParameterNode associated with the output
        """
        parameter = self.add_output(name=name, param_type=param_type)
        node = ActivityParameterNode(parameter=parameter)
        self.nodes.append(node)
        if source:
            self.use_value(source, node)
        else:
            l.warn(
                f"Creating ActivityParameterNode in designate_output() that has no source."
            )
        return node

    def initiating_nodes(self) -> List[ActivityNode]:
        """Find all InitialNode and ActivityParameterNode activities.
        These should be the only activities with no in-flow, which can thus initiate execution.

        Parameters
        ----------
        self: Activity

        Returns
        -------
        List of ActivityNodes able to initiate execution
        """
        return [
            n
            for n in self.nodes
            if isinstance(n, InitialNode)
            or (
                isinstance(n, ActivityParameterNode)
                and n.parameter
                and n.parameter.lookup().property_value.direction == PARAMETER_IN
            )
        ]

    def incoming_edges(self, node: ActivityNode) -> Set[ActivityEdge]:
        """Find the edges that have the designated node as a target

        Parameters
        ----------
        node: target for edges

        Returns
        -------
        Set of ActivityEdges with node as a target
        """
        return {
            e for e in self.edges if e.target == node.identity
        }  # TODO: change to pointer lookup after pySBOL #237

    def outgoing_edges(self, node: ActivityNode) -> Set[ActivityEdge]:
        """Find the edges that have the designated node as a source

        Parameters
        ----------
        node: target for edges

        Returns
        -------
        Set of ActivityEdges with node as a source
        """
        return {
            e for e in self.edges if e.source == node.identity
        }  # TODO: change to pointer lookup after pySBOL #237

    def deconflict_objectflow_sources(self, source: ActivityNode) -> ActivityNode:
        """Avoid nondeterminism in ObjectFlows by injecting ForkNode objects where necessary

        Parameters
        ----------
        self: Activity
        source: node to take a value from, directly or indirectly

        Returns
        -------
        A source to attach to; either the original or an intervening ForkNode
        """
        # Use original if it's one of the node types that supports multiple dispatch
        if isinstance(source, ForkNode) or isinstance(source, DecisionNode):
            return source
        # Otherwise, find out what targets currently attach:
        current_outflows = [e for e in self.edges if e.source.lookup() is source]
        # Use original if nothing is attached to it
        if len(current_outflows) == 0:
            # print(f'No prior use of {source.identity}, connecting directly')
            return source
        # If the flow goes to a single ForkNode, connect to that ForkNode
        elif len(current_outflows) == 1 and isinstance(
            current_outflows[0].target.lookup(), ForkNode
        ):
            # print(f'Found an existing fork from {source.identity}, reusing')
            return current_outflows[0].target.lookup()
        # Otherwise, inject a ForkNode and connect all current flows to that instead
        else:
            # print(f'Found no existing fork from {source.identity}, injecting one')
            fork = ForkNode()
            self.nodes.append(fork)
            self.edges.append(ObjectFlow(source=source, target=fork))
            for f in current_outflows:
                f.source = fork  # change over the existing flows
            return fork

    def call_behavior(self, behavior: Behavior, **input_pin_map):
        """Call a Behavior as an Action in an Activity

        :param behavior: Activity to be invoked (object or name)
        :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
        :return: CallBehaviorAction that invokes the Behavior
        """

        # Any ActivityNode in the pin map will be withheld for connecting via object flows instead
        activity_inputs = {
            k: v
            for k, v in input_pin_map.items()
            if isinstance(v, ActivityNode)
            or (isinstance(v, list) and all([isinstance(vi, ActivityNode) for vi in v]))
        }
        non_activity_inputs = {
            k: v for k, v in input_pin_map.items() if k not in activity_inputs
        }
        cba = self.add_call_behavior_action(behavior, **non_activity_inputs)
        # add flows for activities being connected implicitly
        for name, source in id_sort(activity_inputs.items()):
            sources = source if isinstance(source, list) else [source]
            for source in sources:
                for pin in cba.input_pins(name):
                    # self.use_value(source, cba.input_pin(name))
                    self.use_value(source, pin)
        return cba

    def order(self, source: ActivityNode, target: ActivityNode):
        """Add a ControlFlow between the designated source and target nodes in an Activity

        :param source: ActivityNode that is the source of the control flow
        :param target: ActivityNode that is the target of the control flow
        :return: ControlFlow created between source and target
        """
        if source not in self.nodes:
            raise ValueError(
                f"Source node {source.identity} is not a member of activity {self.identity}"
            )
        if target not in self.nodes:
            raise ValueError(
                f"Target node {target.identity} is not a member of activity {self.identity}"
            )
        flow = ControlFlow(source=source, target=target)
        self.edges.append(flow)
        return flow

    def use_value(self, source: ActivityNode, target: ActivityNode) -> ObjectFlow:
        """Add an ObjectFlow transferring a value between the designated source and target nodes in an Activity

        Typically, these activities will be either Action Pins or ActivityParameterNodes serving as input or output
        :param source: ActivityNode that is the source of the value
        :param target: ActivityNode that receives the value
        :return: ObjectFlow created between source and target
        """
        if (
            source.get_toplevel() is not self
        ):  # check via toplevel, because pins are not directly in the node list
            raise ValueError(
                f"Source node {source.identity} is not a member of activity {self.identity}"
            )
        if target.get_toplevel() is not self:
            raise ValueError(
                f"Target node {target.identity} is not a member of activity {self.identity}"
            )
        source = self.deconflict_objectflow_sources(source)
        flow = ObjectFlow(source=source, target=target)
        self.edges.append(flow)
        return flow

    def use_values(
        self, source: ActivityNode, targets: List[ActivityNode]
    ) -> List[ObjectFlow]:
        return [self.use_value(source, target) for target in targets]

    def add_call_behavior_action(self, behavior: Behavior, **input_pin_literals):
        """Create a call to a Behavior and add it to an Activity

        :param parent: Activity to which the behavior is being added
        :param behavior: Behavior to be called
        :param input_pin_literals: map of literal values to be assigned to specific pins
        :return: newly constructed
        """
        # first, make sure that all of the keyword arguments are in the inputs of the behavior
        unmatched_keys = [
            key
            for key in input_pin_literals.keys()
            if key not in (i.property_value.name for i in behavior.get_inputs())
        ]
        if unmatched_keys:
            raise ValueError(
                f'Specification for "{behavior.display_id}" does not have inputs: {unmatched_keys}'
            )

        # create action
        action = CallBehaviorAction(behavior=behavior)
        self.nodes.append(action)

        # Instantiate input pins
        for i in id_sort(behavior.get_inputs()):
            if i.property_value.name in input_pin_literals:
                # input values might be a collection or singleton
                values = input_pin_literals[i.property_value.name]
                # TODO: type check relationship between value and parameter type specification

                # If the value is a singleton, then wrap it in an iterable
                if not isinstance(values, Iterable) or isinstance(values, str):
                    values = [values]

                # Now create pins for all the input values
                for value in values:
                    if isinstance(value, sbol3.TopLevel) and not value.document:
                        self.document.add(value)
                    action.inputs.append(
                        ValuePin(
                            name=i.property_value.name,
                            is_ordered=i.property_value.is_ordered,
                            is_unique=i.property_value.is_unique,
                            value=literal(value),
                        )
                    )

            else:  # if not a constant, then just a generic InputPin
                action.inputs.append(
                    InputPin(
                        name=i.property_value.name,
                        is_ordered=i.property_value.is_ordered,
                        is_unique=i.property_value.is_unique,
                    )
                )

        # Instantiate output pins
        for o in id_sort(behavior.get_outputs()):
            action.outputs.append(
                OutputPin(
                    name=o.property_value.name,
                    is_ordered=o.property_value.is_ordered,
                    is_unique=o.property_value.is_unique,
                )
            )
        return action

    def validate(self, report: sbol3.ValidationReport = None) -> sbol3.ValidationReport:
        """Checks to see if the activity has any undesirable non-deterministic edges
        Parameters
        ----------
        self
        report

        Returns
        -------

        """
        report = super(Activity, self).validate(report)

        # Check for objects with multiple outgoing ObjectFlow edges that are not of type ForkNode or DecisionNode
        source_counts = Counter(
            [e.source.lookup() for e in self.edges if isinstance(e, ObjectFlow)]
        )
        multi_targets = {
            n: c
            for n, c in source_counts.items()
            if c > 1 and not (isinstance(n, ForkNode) or isinstance(n, DecisionNode))
        }
        for n, c in multi_targets.items():
            report.addWarning(
                n.identity,
                None,
                f"ActivityNode has {c} outgoing edges: multi-edges can cause nondeterministic flow",
            )

        # Check that incoming flow counts obey constraints:
        target_counts = Counter(
            [
                e.target.lookup().unpin()
                for e in self.edges
                if isinstance(e.target.lookup(), ActivityNode)
            ]
        )
        # No InitialNode should have an incoming flow (though an ActivityParameterNode may)
        initial_with_inflow = {
            n: c for n, c in target_counts.items() if isinstance(n, InitialNode)
        }
        for n, c in initial_with_inflow.items():
            report.addError(
                n.identity,
                None,
                f"InitialNode must have no incoming edges, but has {c}",
            )
        # No node besides initiating nodes (InitialNode or ActivityParameterNode) should have no incoming flows
        missing_inflow = (
            set(self.nodes)
            - {n for n, c in target_counts.items()}
            - set(self.initiating_nodes())
        )
        for n in missing_inflow:
            report.addWarning(
                n.identity,
                None,
                f"Node has no incoming edges, so cannot be executed",
            )

        return report

    def to_dot(self, legend=False, ready=[], done=[]):
        def _gv_sanitize(id: str):
            return html.escape(id.replace(":", "_"))

        def _legend():
            fontsize = "10pt"
            legend = graphviz.Digraph(
                name="cluster_Legend",
                graph_attr={
                    "label": "Legend",
                    "shape": "rectangle",
                    "color": "black",
                    "rank": "TB",
                    "fontsize": fontsize,
                },
            )
            legend.node(
                "InitialNode_Legend",
                _attributes={
                    "label": "InitialNode",
                    "fontcolor": "white",
                    "shape": "circle",
                    "style": "filled",
                    "fillcolor": "black",
                    "fontsize": fontsize,
                },
            )
            # legend.node("CallBehaviorAction_Legend", _attributes=_type_attrs(CallBehaviorAction()))
            legend.node(
                "FinalNode_Legend",
                _attributes={
                    "label": "FinalNode",
                    "fontcolor": "white",
                    "shape": "doublecircle",
                    "style": "filled",
                    "fillcolor": "black",
                    "fontsize": fontsize,
                },
            )
            legend.node(
                "ForkNode_Legend",
                _attributes={
                    "label": "ForkNode",
                    "fontcolor": "white",
                    "shape": "rectangle",
                    "height": "0.02",
                    "style": "filled",
                    "fillcolor": "black",
                    "fontsize": fontsize,
                },
            )
            legend.node(
                "MergeNode_Legend",
                _attributes={
                    "label": "MergeNode",
                    "shape": "diamond",
                    "fontsize": fontsize,
                },
            )
            legend.node(
                "ActivityParameterNode_Legend",
                _attributes={
                    "label": "ActivityParameterNode",
                    "shape": "rectangle",
                    "peripheries": "2",
                    "fontsize": fontsize,
                },
            )
            legend.node(
                "CallBehaviorAction_Legend",
                _attributes={
                    "label": f'<<table border="0" cellspacing="0"><tr><td><table border="0" cellspacing="-2"><tr><td> </td><td port="InputPin1" border="1">InputPin</td><td> </td><td port="ValuePin1" border="1">ValuePin: Value</td><td> </td></tr></table></td></tr><tr><td port="node" border="1">CallBehaviorAction</td></tr><tr><td><table border="0" cellspacing="-2"><tr><td> </td><td port="OutputPin1" border="1">OutputPin</td><td> </td></tr></table></td></tr></table>>',
                    "shape": "none",
                    "style": "rounded",
                    "fontsize": fontsize,
                },
            )
            legend.node("a", _attributes={"style": "invis"})
            legend.node("b", _attributes={"style": "invis"})
            legend.node("c", _attributes={"style": "invis"})
            legend.node("d", _attributes={"style": "invis"})
            legend.edge(
                "a",
                "b",
                label="uml.ControlFlow",
                _attributes={"color": "blue", "fontsize": fontsize},
            )
            legend.edge(
                "c",
                "d",
                label="uml.ObjectFlow",
                _attributes={"fontsize": fontsize},
            )
            legend.edge(
                "InitialNode_Legend",
                "FinalNode_Legend",
                _attributes={"style": "invis"},
            )
            legend.edge(
                "FinalNode_Legend",
                "ForkNode_Legend",
                _attributes={"style": "invis"},
            )
            legend.edge(
                "ForkNode_Legend",
                "MergeNode_Legend",
                _attributes={"style": "invis"},
            )
            legend.edge(
                "MergeNode_Legend",
                "ActivityParameterNode_Legend",
                _attributes={"style": "invis"},
            )
            legend.edge(
                "ActivityParameterNode_Legend",
                "CallBehaviorAction_Legend",
                _attributes={"style": "invis"},
            )
            legend.edge(
                "CallBehaviorAction_Legend", "a", _attributes={"style": "invis"}
            )
            legend.edge("b", "c", _attributes={"style": "invis"})
            return legend

        def _label(object: sbol3.Identified):
            truncated = _gv_sanitize(object.identity.replace(f"{self.namespace}", ""))
            in_struct = "_".join(truncated.split("/", 1)).replace(
                "/", ":"
            )  # Replace last "/" with "_"
            return in_struct  # _gv_sanitize(object.identity.replace(f'{self.identity}/', ''))

        def _param_str(param: Parameter) -> str:
            return f"{param.name}"

        def _inpin_str(pin: InputPin) -> str:
            if isinstance(pin, ValuePin):
                if isinstance(pin.value, LiteralReference):
                    literal = pin.value.value.lookup()
                else:
                    literal = pin.value.value
                if isinstance(literal, sbol3.Measure):
                    # TODO: replace kludge with something nicer
                    if literal.unit.startswith(
                        "http://www.ontology-of-units-of-measure.org"
                    ):
                        unit = tyto.OM.get_term_by_uri(literal.unit)
                    else:
                        unit = literal.unit.rsplit("/", maxsplit=1)[1]
                    val_str = f"{literal.value} {unit}"
                elif isinstance(literal, sbol3.Identified):
                    val_str = literal.name or literal.display_id
                elif (
                    isinstance(literal, str)
                    or isinstance(literal, int)
                    or isinstance(literal, bool)
                ):
                    # FIXME: For longer strings, it would be better to left-justify than to center, but I have
                    # no great ideas about how to tell when that applies.
                    val_str = (
                        html.escape(str(literal)).lstrip("\n").replace("\n", "<br/>")
                    )
                elif not literal:
                    return "None"
                else:
                    raise ValueError(
                        f"Do not know how to render literal value {literal} for pin {pin.name}"
                    )
                return f"{pin.name}: {val_str}"
            else:
                return pin.name

        def _fill_color(object: ActivityNode, ready, done):
            # Ready nodes are typically designated by the ExecutionEngine and this will highlight them
            if object in ready:
                color = "green"
            elif object in done:
                color = "blue"
            elif isinstance(object, CallBehaviorAction) or isinstance(
                object, DecisionNode
            ):
                color = "white"
            else:
                color = "black"
            return color

        def _type_attrs(object: ActivityNode, ready, done) -> Dict[str, str]:
            """Get an appropriate set of properties for rendering a GraphViz node.
            Note that while these try to stay close to UML, the limits of GraphViz make us deviate in some cases

            :param object: object to be rendered
            :return: dict of attribute/value pairs
            """
            node_attrs = None
            subgraph = None

            color = _fill_color(object, ready, done)

            if isinstance(object, InitialNode):
                node_attrs = {
                    "label": "",
                    "shape": "circle",
                    "style": "filled",
                    "fillcolor": color,
                }
            elif isinstance(object, FinalNode):
                node_attrs = {
                    "label": "",
                    "shape": "doublecircle",
                    "style": "filled",
                    "fillcolor": color,
                }
            elif isinstance(object, ForkNode) or isinstance(object, JoinNode):
                node_attrs = {
                    "label": "",
                    "shape": "rectangle",
                    "height": "0.02",
                    "style": "filled",
                    "fillcolor": color,
                }
            elif isinstance(object, MergeNode) or isinstance(object, DecisionNode):
                node_attrs = {
                    "label": "",
                    "shape": "diamond",
                    "fillcolor": color,
                }
            elif isinstance(object, ObjectNode):
                if isinstance(object, ActivityParameterNode):
                    label = object.parameter.lookup().property_value.name
                else:
                    raise ValueError(
                        f"Do not know what GraphViz label to use for {object}"
                    )
                node_attrs = {
                    "label": label,
                    "shape": "rectangle",
                    "peripheries": "2",
                    "fillcolor": color,
                }
            elif isinstance(object, ExecutableNode):
                if isinstance(
                    object, CallBehaviorAction
                ):  # render as an HMTL table with pins above/below call
                    port_row = '  <tr><td><table border="0" cellspacing="-2"><tr><td> </td>{}<td> </td></tr></table></td></tr>\n'
                    required_inputs = object.behavior.lookup().get_required_inputs()
                    used_inputs = [
                        o
                        for o in object.inputs
                        if isinstance(o, ValuePin) or self.incoming_edges(o)
                    ]
                    unsat_inputs = [
                        o.property_value
                        for o in required_inputs
                        if o.property_value.name not in [i.name for i in used_inputs]
                    ]
                    in_ports = "<td> </td>".join(
                        f'<td port="{i.display_id}" border="1">{_inpin_str(i)}</td>'
                        for i in used_inputs
                    )
                    unsat_in_ports = "<td> </td>".join(
                        f'<td port="{i.display_id}" bgcolor="red" border="1">{_param_str(i)}</td>'
                        for i in unsat_inputs
                    )
                    in_row = (
                        port_row.format(in_ports + "<td> </td>" + unsat_in_ports)
                        if in_ports or unsat_in_ports
                        else ""
                    )
                    out_ports = "<td> </td>".join(
                        f'<td port="{o.display_id}" border="1">{o.name}</td>'
                        for o in object.outputs
                    )
                    out_row = port_row.format(out_ports) if out_ports else ""

                    node_row = f'  <tr><td port="node" bgcolor="{color}" border="1">{object.behavior.lookup().display_id}</td></tr>\n'
                    table_template = (
                        '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
                    )
                    label = table_template.format(in_row, node_row, out_row)
                    shape = "none"

                    behavior = object.behavior.lookup()
                    if isinstance(behavior, Activity):
                        subgraph = behavior.to_dot(done=done, ready=ready)
                else:
                    raise ValueError(
                        f"Do not know what GraphViz label to use for {object}"
                    )
                node_attrs = {
                    "label": label,
                    "shape": shape,
                    "style": "rounded",
                    "fillcolor": color,
                }
            else:
                raise ValueError(
                    f"Do not know what GraphViz attributes to use for {object}"
                )

            return node_attrs, subgraph

        parent = None
        try:
            parent = graphviz.Digraph(name="_root")
            parent.attr(compound="true")
            subname = _gv_sanitize(self.identity.replace(self.namespace, ""))
            dot = graphviz.Digraph(
                name=f"cluster_{subname}",
                graph_attr={"label": self.name, "shape": "box"},
            )
            if legend:
                dot.subgraph(_legend())

            for edge in self.edges:
                src_id = _label(edge.source.lookup())  # edge.source.replace(":", "_")
                dest_id = _label(edge.target.lookup())  # edge.target.replace(":", "_")
                edge_id = _label(edge)  # edge.identity.replace(":", "_")
                if isinstance(edge.target.lookup(), CallBehaviorAction):
                    dest_id = f"{dest_id}:node"
                if isinstance(edge.source.lookup(), CallBehaviorAction):
                    src_id = f"{src_id}:node"

                source = self.document.find(edge.source)
                if isinstance(source, Pin):
                    try:
                        src_activity = source.get_parent()
                        # dot.edge(_label(src_activity), src_id, label=f"{source.name}")
                        # src_activity = source.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                        # dot.edge(src_activity.replace(":", "_"), src_id, label=f"{source.name}")
                    except Exception as e:
                        print(f"Cannot find source activity for {source.identity}")
                target = self.document.find(edge.target)
                if isinstance(target, Pin):
                    try:
                        dest_activity = target.get_parent()
                        # dot.edge(dest_id, _label(dest_activity), label=f"{target.name}")
                        # dest_activity = target.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                        # dot.edge(dest_id, dest_activity.replace(":", "_"), label=f"{target.name}")
                    except Exception as e:
                        print(f"Cannot find source activity for {source.identity}")

                # dot.node(src_id, label=_name_to_label(src_id))
                # dot.node(dest_id, label=_name_to_label(dest_id))
                # dot.node(edge_id, label=edge_id)
                color = "blue" if isinstance(edge, ControlFlow) else "black"
                if isinstance(source, DecisionNode) and hasattr(edge, "guard"):
                    label = (
                        edge.guard.value
                        if edge.guard
                        and not isinstance(edge.guard, LiteralNull)
                        and edge.guard.value is not None
                        else "None"
                    )
                    label = (
                        "Else"
                        if label == "http://bioprotocols.org/uml#else"
                        else str(label)
                    )
                    dot.edge(src_id, dest_id, label=label, color=color)
                else:
                    dot.edge(src_id, dest_id, color=color)
            for node in self.nodes:
                node_id = _label(node)
                type_attrs, subgraph = _type_attrs(node, ready, done)
                dot.node(node_id, **type_attrs)
                if subgraph:
                    parent.subgraph(subgraph)
            parent.subgraph(dot)
        except Exception as e:
            print(f"Cannot translate to graphviz: {e}")

        return parent
