import os
import posixpath

from sbol_factory import SBOLFactory
import sbol3

import uml

# Load the ontology and create a Python module called labop_submodule
SBOLFactory(
    "labop_submodule",
    posixpath.join(os.path.dirname(os.path.realpath(__file__)), "labop.ttl"),
    "http://bioprotocols.org/labop#",
)

# Import symbols into the top-level labop module
from labop_submodule import *
from labop.ui import *
from labop.utils import *
from labop.data import *
from labop.sample_maps import *
from labop.primitive_execution import *
from labop.decisions import *
from labop.execution_engine import *
from labop.execution_engine_utils import *


#########################################
# Kludge for getting parents and TopLevels - workaround for pySBOL3 issue #234
# TODO: remove after resolution of https://github.com/SynBioDex/pySBOL3/issues/234
def identified_get_parent(self):
    if self.identity:
        return self.document.find(self.identity.rsplit("/", 1)[0])
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
    return self.last_step if hasattr(self, "last_step") else self.initial()


Protocol.get_last_step = protocol_get_last_step  # Add to class via monkey patch


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


def activity_edge_flow_get_target(self):
    """Find the target node of an edge flow
    Parameters
    ----------
    self

    Returns ActivityNode
    -------

    """
    token_source_node = self.token_source.lookup().node.lookup()
    if self.edge:
        target = self.edge.lookup().target.lookup()
    elif isinstance(
        token_source_node, uml.InputPin
    ):  # Tokens for pins do not have an edge connecting pin to activity
        target = token_source_node.get_parent()
    elif isinstance(token_source_node, uml.CallBehaviorAction) and isinstance(
        token_source_node.behavior.lookup(), labop.Protocol
    ):
        # If no edge (because cannot link to InitialNode), then if source is calling a subprotocol, use subprotocol initial node
        target = token_source_node.behavior.lookup().initial()
    else:
        raise Exception(f"Cannot find the target node of edge flow: {self}")
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
        return (
            ""
            if not parameter.lower_value
            else "(Optional) "
            if parameter.lower_value.value < 1
            else ""
        )

    input_parameter_strs = "\n\t".join(
        [
            f"{parameter.property_value}{mark_optional(parameter.property_value)}"
            for parameter in self.parameters
            if parameter.property_value.direction == uml.PARAMETER_IN
        ]
    )
    input_str = (
        f"Input Parameters:\n\t{input_parameter_strs}"
        if len(input_parameter_strs) > 0
        else ""
    )
    output_parameter_strs = "\n\t".join(
        [
            f"{parameter.property_value}{mark_optional(parameter.property_value)}"
            for parameter in self.parameters
            if parameter.property_value.direction == uml.PARAMETER_OUT
        ]
    )
    output_str = (
        f"Output Parameters:\n\t{output_parameter_strs}"
        if len(output_parameter_strs) > 0
        else ""
    )
    return f"""
Primitive: {self.identity}
'''
{self.description}
'''
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
        ref = pv.value

        # Done dereferencing, now get the actual parameter values
        if isinstance(ref, uml.LiteralSpecification):
            value = ref.get_value()
        elif isinstance(ref, sbol3.Identified):
            value = ref
        else:
            raise TypeError(f"Invalid value for Parameter {name} of type {type(ref)}")

        # TODO: Refactor the parameter_value_map to better support
        # multi-valued parameters. However, refactoring will have
        # downstream effects on BehaviorSpecializations

        if name not in parameter_value_map:
            parameter_value_map[name] = {
                "parameter": pv.parameter.lookup(),
                "value": value,
            }
        else:
            if isinstance(parameter_value_map[name]["value"], list):
                parameter_value_map[name]["value"] += [value]
            else:
                parameter_value_map[name]["value"] = [
                    parameter_value_map[name]["value"],
                    value,
                ]
    return parameter_value_map


BehaviorExecution.parameter_value_map = behavior_execution_parameter_value_map


def protocol_execution_get_ordered_executions(self):
    protocol = self.protocol.lookup()
    try:
        [start_node] = [n for n in protocol.nodes if type(n) is uml.InitialNode]
    except Exception as e:
        raise Exception(f"Protocol {protocol.identity} has no InitialNode")
    [execution_start_node] = [
        x for x in self.executions if x.node == start_node.identity
    ]  # ActivityNodeExecution
    ordered_execution_nodes = []
    current_execution_node = execution_start_node
    while current_execution_node:
        try:
            [current_execution_node] = [
                x
                for x in self.executions
                for f in x.incoming_flows
                if f.lookup().token_source == current_execution_node.identity
            ]
            ordered_execution_nodes.append(current_execution_node)
        except ValueError:
            current_execution_node = None
    return ordered_execution_nodes


ProtocolExecution.get_ordered_executions = protocol_execution_get_ordered_executions


def protocol_execution_get_subprotocol_executions(self):
    ordered_subprotocol_executions = []
    ordered_execution_nodes = self.get_ordered_executions()
    ordered_behavior_nodes = [
        x.node.lookup().behavior.lookup()
        for x in ordered_execution_nodes
        if isinstance(x, CallBehaviorExecution)
    ]
    ordered_subprotocols = [
        x.identity for x in ordered_behavior_nodes if isinstance(x, Protocol)
    ]
    ordered_subprotocol_executions = [
        o
        for x in ordered_subprotocols
        for o in self.document.objects
        if type(o) is ProtocolExecution and o.protocol == x
    ]
    return ordered_subprotocol_executions


ProtocolExecution.get_subprotocol_executions = (
    protocol_execution_get_subprotocol_executions
)


def sample_array_get_sample_names(self: SampleArray):
    sample_dict = json.loads(self.initial_contents)
    return [self.document.find(s).name for s in sample_dict.keys()]


SampleArray.get_sample_names = sample_array_get_sample_names


def sample_array_get_sample(self: SampleArray, sample_name):
    sample_dict = json.loads(self.initial_contents)
    samples = [self.document.find(s) for s in sample_dict.keys()]
    for s in samples:
        if s.name == sample_name:
            return self.document.find(s)
    raise LookupError(
        f"SampleArray does not contain initial contents named {sample_name}"
    )


SampleArray.get_sample = sample_array_get_sample

#########################################
# Library handling
loaded_libraries = {}


def import_library(library: str, extension: str = "ttl", nickname: str = None):
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
        library = posixpath.join(
            os.path.dirname(os.path.realpath(__file__)), f"lib/{library}.{extension}"
        )
    # read in the library and put the document in the library collection
    lib = sbol3.Document()
    lib.read(library, extension)
    loaded_libraries[nickname] = lib


def show_library(library_name: str):
    dashes = "-" * 80
    print(dashes)
    print(f"library: {library_name}")
    doc = labop.loaded_libraries[library_name]
    for primitive in doc.objects:
        print(primitive)
    print(dashes)


def show_libraries():
    primitives = {}
    for lib in labop.loaded_libraries.keys():
        show_library(lib)


def get_primitive(doc: sbol3.Document, name: str, copy_to_doc: bool = True):
    """Get a Primitive for use in the protocol, either already in the document or imported from a linked library

    :param doc: Working document
    :param name: Name of primitive, either displayId or full URI
    :return: Primitive that has been found
    """
    found = doc.find(name)
    if not found:
        found = {n: l.find(name) for (n, l) in loaded_libraries.items() if l.find(name)}
        if len(found) >= 2:
            raise ValueError(
                f'Ambiguous primitive: found "{name}" in multiple libraries: {found.keys()}'
            )
        if len(found) == 0:
            raise ValueError(f'Could not find primitive "{name}" in any library')
        found = next(iter(found.values()))
        if copy_to_doc:
            found = found.copy(doc)
    if not isinstance(found, Primitive):
        raise ValueError(
            f'"{name}" should be a Primitive, but it resolves to a {type(found).__name__}'
        )
    return found


def __str__(self):
    print(f"{self.type}: self.identity")


for symbol in dir():
    if isinstance(symbol, sbol3.Identified):
        symbol.__str__ = __str__


def primitive_inherit_parameters(self, parent_primitive):
    """Add the parameters from parent_primitive to self parameters

    :param parent_primitive: Primitive with parameters to inherit
    """
    for p in parent_primitive.parameters:
        param = p.property_value
        if param.direction == uml.PARAMETER_IN:
            self.add_input(
                param.name,
                param.type,
                optional=(param.lower_value.value == 0),
                default_value=param.default_value,
            )
        elif param.direction == uml.PARAMETER_OUT:
            self.add_output(param.name, param.type)
        else:
            raise Exception(f"Cannot inherit parameter {param.name}")


labop.Primitive.inherit_parameters = primitive_inherit_parameters
