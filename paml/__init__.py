import html
import os
import posixpath
from typing import Dict

import graphviz
import tyto
from sbol_factory import SBOLFactory, UMLFactory
import sbol3

import uml # Note: looks unused, but is used in SBOLFactory

# Load the ontology and create a Python module called paml_submodule
SBOLFactory('paml_submodule',
            posixpath.join(os.path.dirname(os.path.realpath(__file__)),
            'paml.ttl'),
            'http://bioprotocols.org/paml#')

# Import symbols into the top-level paml module
from paml_submodule import *
from paml.ui import *

#########################################
# Kludge for getting parents and TopLevels - workaround for pySBOL3 issue #234
# TODO: remove after resolution of https://github.com/SynBioDex/pySBOL3/issues/234
def identified_get_parent(self):
    if self.identity:
        return self.document.find(self.identity.rsplit('/', 1)[0])
    else:
        return None
sbol3.Identified.get_parent = identified_get_parent


def identified_get_toplevel(self):
    if isinstance(self, sbol3.TopLevel):
        return self
    else:
        parent = self.get_parent()
        if parent:
            return identified_get_toplevel(parent)
        else:
            return None
sbol3.Identified.get_toplevel = identified_get_toplevel


###########################################
# Define extension methods for Protocol

def protocol_get_last_step(self):
    return self.last_step if hasattr(self, 'last_step') else self.initial()
Protocol.get_last_step = protocol_get_last_step # Add to class via monkey patch


def protocol_execute_primitive(self, primitive, **input_pin_map):
    """Create and add an execution of a Primitive to a Protocol

    :param primitive: Primitive to be invoked (object or string name)
    :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
    :return: CallBehaviorAction that invokes the Primitive
    """

    # Convenience converter: if given a string, use it to look up the primitive
    if isinstance(primitive, str):
        primitive = get_primitive(self.document, primitive)
    return self.call_behavior(primitive, **input_pin_map)
Protocol.execute_primitive = protocol_execute_primitive  # Add to class via monkey patch


def protocol_primitive_step(self, primitive: Primitive, **input_pin_map):
    """Use a Primitive as an Action in a Protocol, automatically serialized to follow the last step added

    Note that this will not give a stable order if adding to a Protocol that has been deserialized, since
    information about the order in which steps were created is not stored.
    :param primitive: Primitive to be invoked (object or string name)
    :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
    :return: CallBehaviorAction that invokes the Primitive
    """
    pe = self.execute_primitive(primitive, **input_pin_map)
    self.order(self.get_last_step(), pe)
    self.last_step = pe  # update the last step
    return pe
Protocol.primitive_step = protocol_primitive_step  # Add to class via monkey patch

###############################################################################
#
# Protocol class: execution related functions
#
###############################################################################

def protocol_to_dot(self, legend=False):
    def _gv_sanitize(id: str):
        return html.escape(id.replace(":", "_"))

    def _legend():
        fontsize="10pt"
        legend = graphviz.Digraph(name="cluster_Legend",
                                  graph_attr={
                                      "label" : "Legend",
                                      "shape" : "rectangle",
                                      "color" : "black",
                                      "rank" : "TB",
                                      "fontsize" : fontsize
                                  })
        legend.node("InitialNode_Legend", _attributes={'label': 'InitialNode', 'fontcolor' : "white", 'shape': 'circle', 'style': 'filled', 'fillcolor': 'black', "fontsize" : fontsize })
        #legend.node("CallBehaviorAction_Legend", _attributes=_type_attrs(uml.CallBehaviorAction()))
        legend.node("FinalNode_Legend", _attributes={'label': 'FinalNode', 'fontcolor' : "white", 'shape': 'doublecircle', 'style': 'filled', 'fillcolor': 'black', "fontsize" : fontsize})
        legend.node("ForkNode_Legend", _attributes={'label': 'ForkNode', 'fontcolor' : "white", 'shape': 'rectangle', 'height': '0.02', 'style': 'filled', 'fillcolor': 'black', "fontsize" : fontsize})
        legend.node("MergeNode_Legend", _attributes={'label': 'MergeNode', 'shape': 'diamond', "fontsize" : fontsize})
        legend.node("ActivityParameterNode_Legend", _attributes={'label': "ActivityParameterNode", 'shape': 'rectangle', 'peripheries': '2', "fontsize" : fontsize})
        legend.node("CallBehaviorAction_Legend", _attributes={
            "label" : f'<<table border="0" cellspacing="0"><tr><td><table border="0" cellspacing="-2"><tr><td> </td><td port="InputPin1" border="1">InputPin</td><td> </td><td port="ValuePin1" border="1">ValuePin: Value</td><td> </td></tr></table></td></tr><tr><td port="node" border="1">CallBehaviorAction</td></tr><tr><td><table border="0" cellspacing="-2"><tr><td> </td><td port="OutputPin1" border="1">OutputPin</td><td> </td></tr></table></td></tr></table>>',
            "shape" : "none",
            "style": "rounded", "fontsize" : fontsize
        })
        legend.node("a", _attributes={"style": "invis"})
        legend.node("b", _attributes={"style": "invis"})
        legend.node("c", _attributes={"style": "invis"})
        legend.node("d", _attributes={"style": "invis"})
        legend.edge("a", "b", label="uml.ControlFlow", _attributes={"color" : "blue", "fontsize" : fontsize})
        legend.edge("c", "d", label="uml.ObjectFlow", _attributes={"fontsize" : fontsize})
        legend.edge("InitialNode_Legend", "FinalNode_Legend", _attributes={"style" : "invis"})
        legend.edge("FinalNode_Legend", "ForkNode_Legend", _attributes={"style" : "invis"})
        legend.edge("ForkNode_Legend", "MergeNode_Legend", _attributes={"style": "invis"})
        legend.edge("MergeNode_Legend", "ActivityParameterNode_Legend", _attributes={"style": "invis"})
        legend.edge("ActivityParameterNode_Legend", "CallBehaviorAction_Legend", _attributes={"style": "invis"})
        legend.edge("CallBehaviorAction_Legend", "a", _attributes={"style": "invis"})
        legend.edge("b", "c", _attributes={"style": "invis"})
        return legend


    def _label(object: sbol3.Identified):
        truncated = _gv_sanitize(object.identity.replace(f'{self.identity}/', ''))
        in_struct = truncated.replace('/',':')
        return in_struct #_gv_sanitize(object.identity.replace(f'{self.identity}/', ''))

    def _inpin_str(pin: uml.InputPin) -> str:
        if isinstance(pin, uml.ValuePin):
            if isinstance(pin.value, uml.LiteralReference):
                literal = pin.value.value.lookup()
            else:
                literal = pin.value.value
            if isinstance(literal, sbol3.Measure):
                # TODO: replace kludge with something nicer
                if literal.unit.startswith('http://www.ontology-of-units-of-measure.org'):
                    unit = tyto.OM.get_term_by_uri(literal.unit)
                else:
                    unit = literal.unit.rsplit('/',maxsplit=1)[1]
                val_str = f'{literal.value} {unit}'
            elif isinstance(literal, sbol3.Identified):
                val_str = literal.name or literal.display_id
            elif isinstance(literal, str) or isinstance(literal, int) or isinstance(literal, flow) or isinstance(literal, bool):
                # FIXME: For longer strings, it would be better to left-justify than to center, but I have
                # no great ideas about how to tell when that applies.
                val_str = html.escape(str(literal)).lstrip('\n').replace('\n', '<br/>')
            else:
                raise ValueError(f'Do not know how to render literal value {literal}')
            return f'{pin.name}: {val_str}'
        else:
            return pin.name

    def _type_attrs(object: uml.ActivityNode) -> Dict[str,str]:
        """Get an appropriate set of properties for rendering a GraphViz node.
        Note that while these try to stay close to UML, the limits of GraphViz make us deviate in some cases

        :param object: object to be rendered
        :return: dict of attribute/value pairs
        """
        if isinstance(object, uml.InitialNode):
            return {'label': '', 'shape': 'circle', 'style': 'filled', 'fillcolor': 'black' }
        elif isinstance(object, uml.FinalNode):
            return {'label': '', 'shape': 'doublecircle', 'style': 'filled', 'fillcolor': 'black'}
        elif isinstance(object, uml.ForkNode) or isinstance(object, uml.JoinNode):
            return {'label': '', 'shape': 'rectangle', 'height': '0.02', 'style': 'filled', 'fillcolor': 'black'}
        elif isinstance(object, uml.MergeNode) or isinstance(object, uml.DecisionNode):
            return {'label': '', 'shape': 'diamond'}
        elif isinstance(object, uml.ObjectNode):
            if isinstance(object, uml.ActivityParameterNode):
                label = object.parameter.lookup().property_value.name
            else:
                raise ValueError(f'Do not know what GraphViz label to use for {object}')
            return {'label': label, 'shape': 'rectangle', 'peripheries': '2'}
        elif isinstance(object, uml.ExecutableNode):
            if isinstance(object, uml.CallBehaviorAction): # render as an HMTL table with pins above/below call
                port_row = '  <tr><td><table border="0" cellspacing="-2"><tr><td> </td>{}<td> </td></tr></table></td></tr>\n'
                used_inputs = [o for o in object.inputs if isinstance(o,uml.ValuePin) or self.incoming_edges(o)]
                in_ports = '<td> </td>'.join(f'<td port="{i.display_id}" border="1">{_inpin_str(i)}</td>' for i in used_inputs)
                in_row = port_row.format(in_ports) if in_ports else ''
                out_ports = '<td> </td>'.join(f'<td port="{o.display_id}" border="1">{o.name}</td>' for o in object.outputs)
                out_row = port_row.format(out_ports) if out_ports else ''

                node_row = f'  <tr><td port="node" border="1">{object.behavior.lookup().display_id}</td></tr>\n'
                table_template = '<<table border="0" cellspacing="0">\n{}{}{}</table>>'
                label = table_template.format(in_row,node_row,out_row)
                shape = 'none'
            else:
                raise ValueError(f'Do not know what GraphViz label to use for {object}')
            return {'label': label, 'shape': shape, 'style': 'rounded'}
        else:
            raise ValueError(f'Do not know what GraphViz attributes to use for {object}')

    try:
        parent = graphviz.Digraph(name='_root')
        parent.attr(compound='true')
        dot = graphviz.Digraph(name=f'cluster_{_gv_sanitize(self.identity)}',
                               graph_attr={
                                   'label': self.name,
                                   'shape': 'box'
                               })
        if legend:
            dot.subgraph(_legend())

        for edge in self.edges:
            src_id = _label(edge.source.lookup()) #edge.source.replace(":", "_")
            dest_id = _label(edge.target.lookup()) #edge.target.replace(":", "_")
            edge_id = _label(edge) #edge.identity.replace(":", "_")
            if isinstance(edge.target.lookup(), uml.CallBehaviorAction):
                dest_id = f'{dest_id}:node'
            if isinstance(edge.source.lookup(), uml.CallBehaviorAction):
                src_id = f'{src_id}:node'

            source = self.document.find(edge.source)
            if isinstance(source, uml.Pin):
                try:
                    src_activity = source.get_parent()
                    #dot.edge(_label(src_activity), src_id, label=f"{source.name}")
                    #src_activity = source.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                    #dot.edge(src_activity.replace(":", "_"), src_id, label=f"{source.name}")
                except Exception as e:
                    print(f"Cannot find source activity for {source.identity}")
            target = self.document.find(edge.target)
            if isinstance(target, uml.Pin):
                try:
                    dest_activity = target.get_parent()
                    #dot.edge(dest_id, _label(dest_activity), label=f"{target.name}")
                    #dest_activity = target.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                    #dot.edge(dest_id, dest_activity.replace(":", "_"), label=f"{target.name}")
                except Exception as e:
                    print(f"Cannot find source activity for {source.identity}")

            #dot.node(src_id, label=_name_to_label(src_id))
            #dot.node(dest_id, label=_name_to_label(dest_id))
            #dot.node(edge_id, label=edge_id)
            color = 'blue' if isinstance(edge, uml.ControlFlow) else 'black'
            dot.edge(src_id, dest_id, color=color)
        for node in self.nodes:
            node_id = _label(node)
            dot.node(node_id, **_type_attrs(node))

    except Exception as e:
        print(f"Cannot translate to graphviz: {e}")
    parent.subgraph(dot)
    return parent
Protocol.to_dot = protocol_to_dot

def activity_edge_flow_get_target(self):
    '''Find the target node of an edge flow
        Parameters
        ----------
        self

        Returns ActivityNode
        -------

        '''
    if self.edge:
        target = self.document.find(self.document.find(self.edge).target)
    else: # Tokens for pins do not have an edge connecting pin to activity
        target = self.document.find(self.document.find(self.token_source).node).get_parent()
    return target
ActivityEdgeFlow.get_target = activity_edge_flow_get_target

# # Create and add an execution of a subprotocol to a protocol
# def protocol_execute_subprotocol(self, protocol: Protocol, **input_pin_map):
#     # strip any activities in the pin map, which will be held for connecting via flows instead
#     activity_inputs = {k: v for k, v in input_pin_map.items() if isinstance(v,Activity)}
#     non_activity_inputs = {k: v for k, v in input_pin_map.items() if k not in activity_inputs}
#     sub = make_CallBehaviorAction(protocol, **non_activity_inputs)
#     self.activities.append(sub)
#     # add flows for activities being connected implicitly
#     for k,v in activity_inputs.items():
#         self.use_value(v, sub.input_pin(k))
#     return sub
# # Monkey patch:
# Protocol.execute_subprotocol = protocol_execute_subprotocol

def primitive_str(self):
    """
    Create a human readable string describing the Primitive
    :param self:
    :return: str
    """
    def mark_optional(parameter):
        return "(Optional) " if parameter.lower_value.value < 1 else ""

    input_parameter_strs = "\n\t".join([f"{parameter.property_value}{mark_optional(parameter.property_value)}"
                                        for parameter in self.parameters
                                        if parameter.property_value.direction == uml.PARAMETER_IN])
    input_str = f"Input Parameters:\n\t{input_parameter_strs}" if len(input_parameter_strs) > 0 else ""
    output_parameter_strs = "\n\t".join([f"{parameter.property_value}{mark_optional(parameter.property_value)}"
                                        for parameter in self.parameters
                                        if parameter.property_value.direction == uml.PARAMETER_OUT])
    output_str = f"Output Parameters:\n\t{output_parameter_strs}" if len(output_parameter_strs) > 0 else ""
    return f"""
Primitive: {self.identity}
{input_str}
{output_str}
            """
Primitive.__str__ = primitive_str


def behavior_execution_parameter_value_map(self):
    """
    Return a dictionary mapping parameter names to value or (value, unit)
    :param self:
    :return:
    """
    parameter_value_map = {}

    for pv in self.parameter_values:
        name = pv.parameter.lookup().property_value.name
        if isinstance(pv.value, uml.LiteralReference):
            ref = pv.value.value.lookup()
            value = ref.value if isinstance(ref, uml.LiteralSpecification) else ref
            unit = ref.unit if isinstance(ref, uml.LiteralSpecification) and hasattr(ref, "unit") else None
        else:
            value = pv.value.value
            unit = pv.value.unit if hasattr(pv.value, "unit") else None

        parameter_value_map[name] = {"parameter" : pv.parameter.lookup(),
                                     "value" : (value, unit) if unit else value}
    return parameter_value_map
BehaviorExecution.parameter_value_map = behavior_execution_parameter_value_map


#########################################
# Library handling
loaded_libraries = {}


def import_library(library: str, extension: str = 'ttl', nickname: str = None):
    """Import a library of primitives and make it available for use in defining a protocol.

    Note that the actual contents of a library are added into a protocol document lazily, only as they're actually used
    TODO: this needs to be generalized to a notion of load paths, to allow other than built-in libraries

    :param library: name of library file to load
    :param extension: Format of library; defaults to ttl
    :param nickname: Name to load the library under; defaults to library name
    :return: Nothing
    """
    if not nickname:
        nickname = library
    if not os.path.isfile(library):
        library = posixpath.join(os.path.dirname(os.path.realpath(__file__)), f'lib/{library}.{extension}')
    # read in the library and put the document in the library collection
    lib = sbol3.Document()
    lib.read(library, extension)
    loaded_libraries[nickname] = lib


def get_primitive(doc: sbol3.Document, name: str):
    """Get a Primitive for use in the protocol, either already in the document or imported from a linked library

    :param doc: Working document
    :param name: Name of primitive, either displayId or full URI
    :return: Primitive that has been found
    """
    found = doc.find(name)
    if not found:
        found = {n: l.find(name) for (n, l) in loaded_libraries.items() if l.find(name)}
        if len(found) >= 2:
            raise ValueError(f'Ambiguous primitive: found "{name}" in multiple libraries: {found.keys()}')
        if len(found) == 0:
            raise ValueError(f'Could not find primitive "{name}" in any library')
        found = next(iter(found.values())).copy(doc)
    if not isinstance(found, Primitive):
        raise ValueError(f'"{name}" should be a Primitive, but it resolves to a {type(found).__name__}')
    return found
