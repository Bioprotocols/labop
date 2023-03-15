"""
The CallBehaviorAction class defines the functions corresponding to the dynamically generated labop class CallBehaviorAction
"""

import sbol3

import uml.inner as inner

from .call_action import CallAction
from .literal_reference import LiteralReference
from .utils import inner_to_outer, literal


class CallBehaviorAction(inner.CallBehaviorAction, CallAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def input_pin(self, pin_name: str):
        """Find an input pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.inputs if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(
                f"Could not find input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        if len(pin_set) > 1:
            raise ValueError(
                f"Found more than one input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        return pin_set.pop()

    def input_pins(self, pin_name: str):
        """Find an input pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.inputs if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(
                f"Could not find input pin named {pin_name} for Primitive {self.behavior.lookup().display_id}"
            )
        return pin_set

    def output_pin(self, pin_name: str):
        """Find an output pin on the action with the specified name

        :param pin_name:
        :return: Pin with specified name
        """
        pin_set = {x for x in self.outputs if x.name == pin_name}
        if len(pin_set) == 0:
            raise ValueError(f"Could not find output pin named {pin_name}")
        if len(pin_set) > 1:
            raise ValueError(f"Found more than one output pin named {pin_name}")
        return pin_set.pop()

    def pin_parameter(self, pin_name: str):
        """Find the behavior parameter corresponding to the pin

        :param pin_name:
        :return: Parameter with specified name
        """
        try:
            pins = self.input_pins(pin_name)
        except:
            try:
                pin = self.output_pin(pin_name)
            except:
                raise ValueError(f"Could not find pin named {pin_name}")
        behavior = self.behavior.lookup()
        parameters = [
            p for p in behavior.parameters if p.property_value.name == pin_name
        ]
        if len(parameters) == 0:
            raise ValueError(
                f"Invalid parameter {pin_name} provided for Primitive {behavior.display_id}"
            )
        elif len(parameters) > 1:
            raise ValueError(
                f"Primitive {behavior.display_id} has multiple Parameters with the same name"
            )
        parameter = parameters[0]
        try:
            parameter.__class__ = inner_to_outer(parameter)
        except:
            pass
        try:
            parameter.property_value.__class__ = inner_to_outer(
                parameter.property_value
            )
        except:
            pass
        return parameter

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
