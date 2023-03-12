import html
from typing import Dict

import graphviz
import sbol3
import tyto

from uml import *


def activity_node_dot_attrs(self):
    return {"label": "", "shape": "circle"}


ActivityNode.dot_attrs = activity_node_dot_attrs  # Add to class via monkey patch


def initial_node_dot_attrs(self):
    return {"label": "", "shape": "circle", "style": "filled", "fillcolor": "black"}


InitialNode.dot_attrs = initial_node_dot_attrs  # Add to class via monkey patch


def final_node_dot_attrs(self):
    return {
        "label": "",
        "shape": "doublecircle",
        "style": "filled",
        "fillcolor": "black",
    }


FinalNode.dot_attrs = final_node_dot_attrs  # Add to class via monkey patch


def join_node_dot_attrs(self):
    return {
        "label": "",
        "shape": "rectangle",
        "height": "0.02",
        "style": "filled",
        "fillcolor": "black",
    }


JoinNode.dot_attrs = join_node_dot_attrs  # Add to class via monkey patch


def fork_node_dot_attrs(self):
    return {
        "label": "",
        "shape": "rectangle",
        "height": "0.02",
        "style": "filled",
        "fillcolor": "black",
    }


ForkNode.dot_attrs = fork_node_dot_attrs  # Add to class via monkey patch


def merge_node_dot_attrs(self):
    return {"label": "", "shape": "diamond"}


MergeNode.dot_attrs = merge_node_dot_attrs  # Add to class via monkey patch


def decision_node_dot_attrs(self):
    return {"label": "", "shape": "diamond"}


DecisionNode.dot_attrs = decision_node_dot_attrs  # Add to class via monkey patch


def object_node_dot_attrs(self):
    raise ValueError(f"Do not know what GraphViz label to use for {self}")


ObjectNode.dot_attrs = object_node_dot_attrs  # Add to class via monkey patch


def input_pin_dot_attrs(self):
    return {}


InputPin.dot_attrs = input_pin_dot_attrs  # Add to class via monkey patch


def activity_parameter_node_dot_attrs(self):
    label = self.parameter.lookup().name
    return {"label": label, "shape": "rectangle", "peripheries": "2"}


ActivityParameterNode.dot_attrs = (
    activity_parameter_node_dot_attrs  # Add to class via monkey patch
)


def executable_node_dot_attrs(self):
    raise ValueError(f"Do not know what GraphViz label to use for {self}")


ExecutableNode.dot_attrs = executable_node_dot_attrs  # Add to class via monkey patch


def call_behavior_action_node_dot_attrs(self):
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


CallBehaviorAction.dot_attrs = (
    call_behavior_action_node_dot_attrs  # Add to class via monkey patch
)


def input_pin_dot_node_name(self):
    return self.name


InputPin.dot_node_name = input_pin_dot_node_name  # Add to class via monkey patch


def value_pin_dot_node_name(self):
    literal_str = self.value.dot_value()
    return f"{self.name}: {literal_str}"


ValuePin.dot_node_name = value_pin_dot_node_name  # Add to class via monkey patch


def literal_string_dot_value(self):
    return self.value


LiteralString.dot_value = literal_string_dot_value  # Add to class via monkey patch


def literal_integer_dot_value(self):
    return str(self.value)


LiteralInteger.dot_value = literal_integer_dot_value  # Add to class via monkey patch


def literal_boolean_dot_value(self):
    return str(self.value)


LiteralBoolean.dot_value = literal_boolean_dot_value  # Add to class via monkey patch


def literal_real_dot_value(self):
    return str(self.value)


LiteralReal.dot_value = literal_real_dot_value  # Add to class via monkey patch


def literal_identified_dot_value(self):
    literal = self.value
    if isinstance(literal, sbol3.Measure):
        # TODO: replace kludge with something nicer
        if literal.unit.startswith("http://www.ontology-of-units-of-measure.org"):
            unit = tyto.OM.get_term_by_uri(literal.unit)
        else:
            unit = literal.unit.rsplit("/", maxsplit=1)[1]
        val_str = f"{literal.value} {unit}"
    else:
        val_str = literal.name or literal.display_id
    return val_str


LiteralIdentified.dot_value = (
    literal_identified_dot_value  # Add to class via monkey patch
)


def literal_reference_dot_value(self):
    literal = self.value.lookup()
    if isinstance(literal, sbol3.Measure):
        # TODO: replace kludge with something nicer
        if literal.unit.startswith("http://www.ontology-of-units-of-measure.org"):
            unit = tyto.OM.get_term_by_uri(literal.unit)
        else:
            unit = literal.unit.rsplit("/", maxsplit=1)[1]
        val_str = f"{literal.value} {unit}"
    else:
        val_str = literal.name or literal.display_id
    return val_str


LiteralReference.dot_value = (
    literal_reference_dot_value  # Add to class via monkey patch
)


def _gv_sanitize(id: str):
    return html.escape(id.replace(":", "_"))


def identified_dot_label(self, parent_identity=None):
    truncated = _gv_sanitize(
        self.identity.replace(f"{parent_identity.lookup().namespace}", "")
    )
    in_struct = "_".join(truncated.split("/", 1)).replace("/", ":")
    return in_struct


sbol3.Identified.dot_label = identified_dot_label  # Add to class via monkey patch


def parameter_str(self):
    """
    Create a human readable string for a parameter.
    :param self:
    :return: str
    """
    default_value_str = f"= {self.default_value}" if self.default_value else ""
    return f"""{self.name}: {self.type} {default_value_str}"""


Parameter.__str__ = parameter_str


def parameter_template(self):
    """
    Create a template for a parameter. Used for populating UI elements.
    :param self:
    :return: str
    """
    default_value_str = f"= {self.default_value}" if self.default_value else ""
    return f"""{self.name}=\'{default_value_str}\'"""


Parameter.template = parameter_template


def activity_to_dot(self, legend=False, ready=[], done=[]):
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
            "c", "d", label="uml.ObjectFlow", _attributes={"fontsize": fontsize}
        )
        legend.edge(
            "InitialNode_Legend", "FinalNode_Legend", _attributes={"style": "invis"}
        )
        legend.edge(
            "FinalNode_Legend", "ForkNode_Legend", _attributes={"style": "invis"}
        )
        legend.edge(
            "ForkNode_Legend", "MergeNode_Legend", _attributes={"style": "invis"}
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
        legend.edge("CallBehaviorAction_Legend", "a", _attributes={"style": "invis"})
        legend.edge("b", "c", _attributes={"style": "invis"})
        return legend

    def _label(object: sbol3.Identified):
        truncated = _gv_sanitize(object.identity.replace(f"{self.namespace}", ""))
        in_struct = "_".join(truncated.split("/", 1)).replace(
            "/", ":"
        )  # Replace last "/" with "_"
        return (
            in_struct  # _gv_sanitize(object.identity.replace(f'{self.identity}/', ''))
        )

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
                val_str = html.escape(str(literal)).lstrip("\n").replace("\n", "<br/>")
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
        elif isinstance(object, CallBehaviorAction) or isinstance(object, DecisionNode):
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
            node_attrs = {"label": "", "shape": "diamond", "fillcolor": color}
        elif isinstance(object, ObjectNode):
            if isinstance(object, ActivityParameterNode):
                label = object.parameter.lookup().property_value.name
            else:
                raise ValueError(f"Do not know what GraphViz label to use for {object}")
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
                table_template = '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
                label = table_template.format(in_row, node_row, out_row)
                shape = "none"

                behavior = object.behavior.lookup()
                if isinstance(behavior, Activity):
                    subgraph = behavior.to_dot(done=done, ready=ready)
            else:
                raise ValueError(f"Do not know what GraphViz label to use for {object}")
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
            name=f"cluster_{subname}", graph_attr={"label": self.name, "shape": "box"}
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


Activity.to_dot = activity_to_dot


def input_pin_str(self):
    return self.name


InputPin.__str__ = input_pin_str


def value_pin_str(self):
    return f"{self.name}: {self.value}"


ValuePin.__str__ = value_pin_str


def literal_str(self):
    value = self.get_value()
    if isinstance(value, str) or isinstance(value, int) or isinstance(value, bool):
        val_str = html.escape(str(value)).lstrip("\n").replace("\n", "<br/>")
    else:
        val_str = str(value)
    return val_str


LiteralSpecification.__str__ = literal_str


def measure_str(self):
    if self.unit.startswith("http://www.ontology-of-units-of-measure.org"):
        unit = tyto.OM.get_term_by_uri(self.unit)
    else:
        unit = self.unit.rsplit("/", maxsplit=1)[1]
    return f"{self.value} {unit}"


sbol3.Measure.__str__ = measure_str


def identified_str(self):
    return str(self.name or self.display_id)


sbol3.Identified.__str__ = identified_str
