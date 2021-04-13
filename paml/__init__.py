from sbol_factory import SBOLFactory, Document, ValidationReport, UMLFactory
import sbol3 as sbol
import os
import posixpath

# Import ontology
__factory__ = SBOLFactory(locals(), 
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                         'paml.ttl'),
                          'http://bioprotocols.org/paml#')
__umlfactory__ = UMLFactory(__factory__)

# Define extension methods for Primitive
def primitive_add_input(self, name, type, optional=False):
    pin = PrimitivePinSpecification(name = name, type = type)
    pin.optional = optional
    self.input.append(pin)
    return pin
# Monkey patch
Primitive.add_input = primitive_add_input

def primitive_add_output(self, name, type):
    pin = PrimitivePinSpecification(name = name, type = type)
    self.output.append(pin)
    return pin
# Monkey patch
Primitive.add_output = primitive_add_output

# Executable factory functions (can't override initialization)
def executable_make_pins(self, specification, **input_pin_map):
    # first, make sure that all of the keyword arguments are in the inputs of the selected primitive
    unmatched_keys = [key for key in input_pin_map.keys() if key not in (i.name for i in specification.input)]
    assert not unmatched_keys, ValueError("Specification for '"+specification.display_id+"' does not have inputs: "+str(unmatched_keys))

    # Instantiate input pins
    for pin_spec in specification.input:
        if pin_spec.name not in input_pin_map: # Note: affected by pySBOL3 issue 229
            val = None # if not wired to a constant, it will be a generic Pin
        else:
            val = input_pin_map[pin_spec.name]
            # Turning off type checking for now, since I don't know how to check subclass relations efficiently
            #if val.type_uri != pin_spec.type:
            #    raise TypeError(f'Value for input pin "{pin_spec.name or pin_spec.display_id}" must be of type {pin_spec.type}')

        # Construct Pin of appropriate subtype
        if val:
            if isinstance(val, sbol.TopLevel) or isinstance(val, Location):
                pin = ReferenceValuePin()
            elif isinstance(val, sbol.Identified):
                pin = LocalValuePin()
            else:
                pin = SimpleValuePin()
            pin.value = val
        else:
            pin = Pin()

        # Set properties
        pin.instance_of = pin_spec
        pin.name = pin_spec.name
        if pin_spec.type:
            pin.type = pin_spec.type
        self.input.append(pin)

    # Instantiate output pins
    for pin_spec in specification.output:
        # Construct Pin of appropriate subtype
        pin = Pin()

        # Set properties
        pin.name = pin_spec.name
        pin.instance_of = pin_spec
        self.output.append(pin)
# monkey patch
Executable.make_pins = executable_make_pins

def Executable_input_pin(self, pin_name):
    #pin_set = [x for x in self.input if x.instance_of.lookup().name == pin_name or doc.find(x.instance_of).display_id == pin_name] # note: pySBOL3 issue 229
    pin_set = [x for x in self.input if self.document.find(x.instance_of).name == pin_name or self.document.find(x.instance_of).display_id == pin_name] # workaround for PAML issue #5
    assert len(pin_set)>0, ValueError("Couldn't find input pin named "+pin_name)
    assert len(pin_set)<2, ValueError("Found more than one input pin named "+pin_name)
    return pin_set[0]
Executable.input_pin = Executable_input_pin

def Executable_output_pin(self, pin_name):
    #pin_set = [x for x in self.output if x.instance_of.lookup().name == pin_name or doc.find(x.instance_of).display_id == pin_name] # note: pySBOL3 issue 229
    pin_set = [x for x in self.output if self.document.find(x.instance_of).name == pin_name or self.document.find(x.instance_of).display_id == pin_name] # workaround for PAML issue #5
    assert len(pin_set)>0, ValueError("Couldn't find output pin named "+pin_name)
    assert len(pin_set)<2, ValueError("Found more than one output pin named "+pin_name)
    return pin_set[0]
Executable.output_pin = Executable_output_pin


def make_PrimitiveExecutable(primitive: Primitive, **input_pin_map):
    self = PrimitiveExecutable(instance_of = primitive)
    self.make_pins(primitive, **input_pin_map)
    return self

def make_SubProtocol(protocol: Protocol, **input_pin_map):
    self = SubProtocol(instance_of = protocol)
    self.make_pins(protocol, **input_pin_map)
    return self


########################
# Another helper; this one should probably be added as an extension

def protocol_contains_activity(self, activity):
    return (activity in self.activities) or \
           next((x for x in self.activities if
                 isinstance(x, Executable) and (activity in x.input or activity in x.output)), False)
# Monkey patch:
Protocol.contains_activity = protocol_contains_activity

def Protocol_initial(self):
    initial = [a for a in self.activities if isinstance(a, Initial)]
    if not initial:
        self.activities.append(Initial())
        return Protocol_initial(self)
    elif len(initial)==1:
        return initial[0]
    else:
        raise ValueError("Protocol '"+self.display_id+"'must have only one Initial node, but found "+str(len(initial)))
# Monkey patch:
Protocol.initial = Protocol_initial

def Protocol_final(self):
    final = [a for a in self.activities if isinstance(a, Final)]
    if not final:
        self.activities.append(Final())
        return Protocol_final(self)
    elif len(final)==1:
        return final[0]
    else:
        raise ValueError("Protocol '"+self.display_id+"'must have only one Final node, but found "+str(len(final)))
# Monkey patch:
Protocol.final = Protocol_final

def protocol_add_input(self, name, **kwargs):
    input = Value(name=name, **kwargs)
    self.activities.append(input)
    input_spec = ProtocolPinSpecification(name=name, activity = input)
    self.input.append(input_spec)
    return input
# Monkey patch:
Protocol.add_input = protocol_add_input

def protocol_add_output(self, name, value_source:Activity=None):
    output = Value()
    self.activities.append(output)
    output_spec = ProtocolPinSpecification(name=name, activity = output)
    self.output.append(output_spec)
    if value_source:
        self.add_flow(value_source, output)
    return output
# Monkey patch:
Protocol.add_output = protocol_add_output

# Create and add an execution of a primitive to a protocol
def protocol_execute_primitive(self, primitive: Primitive, **input_pin_map):
    if isinstance(primitive,str):
        primitive = get_primitive(self.document, primitive)
    # strip any activities in the pin map, which will be held for connecting via flows instead
    activity_inputs = {k: v for k, v in input_pin_map.items() if isinstance(v,Activity)}
    non_activity_inputs = {k: v for k, v in input_pin_map.items() if k not in activity_inputs}
    pe = make_PrimitiveExecutable(primitive, **non_activity_inputs)
    self.activities.append(pe)
    # add flows for activities being connected implicitly
    for k,v in activity_inputs.items():
        self.add_flow(v, pe.input_pin(k))
    return pe
# Monkey patch:
Protocol.execute_primitive = protocol_execute_primitive

# Create and add an execution of a subprotocol to a protocol
def protocol_execute_subprotocol(self, protocol: Protocol, **input_pin_map):
    # strip any activities in the pin map, which will be held for connecting via flows instead
    activity_inputs = {k: v for k, v in input_pin_map.items() if isinstance(v,Activity)}
    non_activity_inputs = {k: v for k, v in input_pin_map.items() if k not in activity_inputs}
    sub = make_SubProtocol(protocol, **non_activity_inputs)
    self.activities.append(sub)
    # add flows for activities being connected implicitly
    for k,v in activity_inputs.items():
        self.add_flow(v, sub.input_pin(k))
    return sub
# Monkey patch:
Protocol.execute_subprotocol = protocol_execute_subprotocol

# Create and add a flow between the designated child source and sink activities
def protocol_add_flow(self, source, sink):
    assert self.contains_activity(source), ValueError(
        'Source activity ' + source.identity + ' is not a member of protocol ' + self.identity)
    assert self.contains_activity(sink), ValueError(
        'Sink activity ' + sink.identity + ' is not a member of protocol ' + self.identity)
    flow = Flow(source = source, sink = sink)
    self.flows.append(flow)
    return flow
# Monkey patch:
Protocol.add_flow = protocol_add_flow


#########################################
# Library handling
loaded_libraries = {}

def import_library(library:str, file_format:str = 'ttl', nickname:str=None ):
    if not nickname:
        nickname = library
    if not os.path.isfile(library):
        library = posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                 ('lib/'+library+'.ttl'))
    # read in the library and put the document in the library collection
    lib = sbol.Document()
    lib.read(library, file_format)
    loaded_libraries[nickname] = lib

def get_primitive(doc:sbol.Document, name:str):
    found = doc.find(name)
    if not found:
        found = {n:l.find(name) for (n,l) in loaded_libraries.items() if l.find(name)}
        assert len(found)<2, ValueError("Ambiguous primitive: found '"+name+"' in multiple libraries: "+str(found.keys()))
        assert len(found)>0, ValueError("Couldn't find primitive '"+name+"' in any library")
        found = next(iter(found.values())).copy(doc)
    return found
