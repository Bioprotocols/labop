import graphviz
from sbol_factory import SBOLFactory, UMLFactory
import os
import posixpath
import sbol3
import uml # Note: looks unused, but is used in SBOLFactory

# Load the ontology and create a Python module called paml_submodule
SBOLFactory('paml_submodule',
            posixpath.join(os.path.dirname(os.path.realpath(__file__)),
            'paml.ttl'),
            'http://bioprotocols.org/paml#')

# Import symbols into the top-level paml module
from paml_submodule import *


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

def protocol_initiating_nodes(self):
    """
    Create a set of tokens that correspond to the initial nodes of the protocol.
    :return: set of activity nodes
    """
    initials = [node for node in self.nodes if isinstance(node, uml.InitialNode)]
    return initials
Protocol.initiating_nodes = protocol_initiating_nodes  # Add to class via monkey patch

def protocol_to_dot(self):
    uri = self.identity.replace(":", "_")

    def _name_to_label(name):
        return name.replace(f"_{uri}/", "_").replace(f"{uri}", "protocol")

    try:
        dot = graphviz.Digraph(name=f"cluster_{self.identity}",
                               graph_attr={
                                   "label": self.identity
                               })
        for edge in self.edges:
            src_id = edge.source.replace(":", "_")
            dest_id = edge.target.replace(":", "_")
            edge_id = edge.identity.replace(":", "_")

            source = self.document.find(edge.source)
            if isinstance(source, uml.Pin):
                try:
                    src_activity = source.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                    dot.edge(src_activity.replace(":", "_"), src_id, label=f"{source.name}")
                except Exception as e:
                    print(f"Cannot find source activity for {source.identity}")
            target = self.document.find(edge.target)
            if isinstance(target, uml.Pin):
                try:
                    dest_activity = target.identity.rsplit('/', 1)[0] # Assumes pin is owned by activity
                    dot.edge(dest_id, dest_activity.replace(":", "_"), label=f"{target.name}")
                except Exception as e:
                    print(f"Cannot find source activity for {source.identity}")

            dot.node(src_id, label=_name_to_label(src_id))
            dot.node(dest_id, label=_name_to_label(dest_id))
            dot.node(edge_id, label=_name_to_label(edge_id))
            dot.edge(src_id, edge_id)
            dot.edge(edge_id, dest_id)
        for node in self.nodes:
            node_id = node.identity.replace(":", "_")
            dot.node(node_id, label=_name_to_label(node_id))
    except Exception as e:
        print(f"Cannot translate to graphviz: {e}")
    return dot
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
