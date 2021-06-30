from sbol_factory import SBOLFactory, UMLFactory
import os
import posixpath
import sbol3
import uml # Note: looks unused, but is used in SBOLFactory

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                         'paml.ttl'),
                          'http://bioprotocols.org/paml#')
__umlfactory__ = UMLFactory(__factory__)


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
    last_step = (self.nodes[-1] if self.nodes else self.initial())
    self.order(last_step, pe)
    return pe
Protocol.primitive_step = protocol_primitive_step  # Add to class via monkey patch


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
