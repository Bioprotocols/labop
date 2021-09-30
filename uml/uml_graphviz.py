from uml import *
import tyto
import sbol3

def activity_node_dot_attrs(self):
    return {'label': '', 'shape': 'circle'}
ActivityNode.dot_attrs = activity_node_dot_attrs  # Add to class via monkey patch

def initial_node_dot_attrs(self):
    return {'label': '', 'shape': 'circle', 'style': 'filled', 'fillcolor': 'black'}
InitialNode.dot_attrs = initial_node_dot_attrs  # Add to class via monkey patch

def final_node_dot_attrs(self):
    return {'label': '', 'shape': 'doublecircle', 'style': 'filled', 'fillcolor': 'black'}
FinalNode.dot_attrs = final_node_dot_attrs  # Add to class via monkey patch

def join_node_dot_attrs(self):
    return {'label': '', 'shape': 'rectangle', 'height': '0.02', 'style': 'filled', 'fillcolor': 'black'}
JoinNode.dot_attrs = join_node_dot_attrs  # Add to class via monkey patch

def fork_node_dot_attrs(self):
    return {'label': '', 'shape': 'rectangle', 'height': '0.02', 'style': 'filled', 'fillcolor': 'black'}
ForkNode.dot_attrs = fork_node_dot_attrs  # Add to class via monkey patch

def merge_node_dot_attrs(self):
    return {'label': '', 'shape': 'diamond'}
MergeNode.dot_attrs = merge_node_dot_attrs  # Add to class via monkey patch

def decision_node_dot_attrs(self):
    return {'label': '', 'shape': 'diamond'}
DecisionNode.dot_attrs = decision_node_dot_attrs  # Add to class via monkey patch

def object_node_dot_attrs(self):
    raise ValueError(f'Do not know what GraphViz label to use for {self}')
ObjectNode.dot_attrs = object_node_dot_attrs  # Add to class via monkey patch

def input_pin_dot_attrs(self):
    return {}
InputPin.dot_attrs = input_pin_dot_attrs  # Add to class via monkey patch


def activity_parameter_node_dot_attrs(self):
    label = self.parameter.lookup().name
    return {'label': label, 'shape': 'rectangle', 'peripheries': '2'}
ActivityParameterNode.dot_attrs = activity_parameter_node_dot_attrs  # Add to class via monkey patch

def executable_node_dot_attrs(self):
    raise ValueError(f'Do not know what GraphViz label to use for {self}')
ExecutableNode.dot_attrs = executable_node_dot_attrs  # Add to class via monkey patch

def call_behavior_action_node_dot_attrs(self):
    port_row = '  <tr><td><table border="0" cellspacing="-2"><tr><td> </td>{}<td> </td></tr></table></td></tr>\n'
    in_ports = '<td> </td>'.join(f'<td port="{i.display_id}" border="1">{i.dot_node_name()}</td>' for i in self.inputs)
    in_row = port_row.format(in_ports) if in_ports else ''
    out_ports = '<td> </td>'.join(f'<td port="{o.display_id}" border="1">{o.name}</td>' for o in self.outputs)
    out_row = port_row.format(out_ports) if out_ports else ''

    node_row = f'  <tr><td port="node" border="1">{self.behavior.lookup().display_id}</td></tr>\n'
    table_template = '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
    label = table_template.format(in_row, node_row, out_row)
    shape = 'none'
    return {'label': label, 'shape': shape, 'style': 'rounded'}
CallBehaviorAction.dot_attrs = call_behavior_action_node_dot_attrs  # Add to class via monkey patch


def input_pin_dot_node_name(self):
    return self.name
InputPin.dot_node_name = input_pin_dot_node_name  # Add to class via monkey patch

def value_pin_dot_node_name(self):
    literal_str = self.value.dot_value()
    return f'{self.name}: {literal_str}'
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
        if literal.unit.startswith('http://www.ontology-of-units-of-measure.org'):
            unit = tyto.OM.get_term_by_uri(literal.unit)
        else:
            unit = literal.unit.rsplit('/', maxsplit=1)[1]
        val_str = f'{literal.value} {unit}'
    else:
        val_str = literal.name or literal.display_id
    return val_str
LiteralIdentified.dot_value = literal_identified_dot_value  # Add to class via monkey patch

def literal_reference_dot_value(self):
    literal = self.value.lookup()
    if isinstance(literal, sbol3.Measure):
        # TODO: replace kludge with something nicer
        if literal.unit.startswith('http://www.ontology-of-units-of-measure.org'):
            unit = tyto.OM.get_term_by_uri(literal.unit)
        else:
            unit = literal.unit.rsplit('/', maxsplit=1)[1]
        val_str = f'{literal.value} {unit}'
    else:
        val_str = literal.name or literal.display_id
    return val_str
LiteralReference.dot_value = literal_reference_dot_value  # Add to class via monkey patch


def _gv_sanitize(id: str):
    return id.replace(":", "_")

def identified_dot_label(self, parent_identity=None):
    truncated = _gv_sanitize(self.identity.replace(f'{parent_identity}/', ''))
    in_struct = truncated.replace('/', ':')
    return in_struct
sbol3.Identified.dot_label = identified_dot_label   # Add to class via monkey patch

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