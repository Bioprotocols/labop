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
    pin = PinSpecification()
    pin.name = name
    pin.type = type
    pin.optional = optional
    self.input.append(pin)
# Monkey patch
Primitive.add_input = primitive_add_input

def primitive_add_output(self, name, type):
    pin = PinSpecification()
    pin.name = name
    pin.type = type
    self.output.append(pin)
# Monkey patch
Primitive.add_output = primitive_add_output

# PrimitiveExecutable factory function (can't override iterator)
def make_PrimitiveExecutable(primitive: Primitive, **input_pin_map):
    # first, make sure that all of the keyword arguments are in the inputs of the selected primitive
    unmatched_keys = [key for key in input_pin_map.keys() if key not in (i.name for i in primitive.input)]
    assert not unmatched_keys, ValueError("Primitive '"+primitive.display_id+"' does not have specified keys: "+str(unmatched_keys))

    self = PrimitiveExecutable()

    # link to primitive prototype
    self.instance_of = primitive

    # Instantiate input pins
    for pin_spec in primitive.input:
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
            else:
                pin = LocalValuePin()
            pin.value = val
        else:
            pin = Pin()

        # Set properties
        pin.instance_of = pin_spec
        pin.name = pin_spec.name
        pin.type = pin_spec.type
        self.input.append(pin)

    # Instantiate output pins
    for pin_spec in primitive.output:
        # Construct Pin of appropriate subtype
        pin = Pin()

        # Set properties
        pin.name = pin_spec.name
        pin.instance_of = pin_spec
        self.output.append(pin)

    return self

def PrimitiveExecutable_input_pin(self, pin_name, doc):
    #pin_set = [x for x in self.input if x.instance_of.lookup().name == pin_name or doc.find(x.instance_of).display_id == pin_name] # note: pySBOL3 issue 229
    pin_set = [x for x in self.input if doc.find(x.instance_of).name == pin_name or doc.find(x.instance_of).display_id == pin_name] # workaround for PAML issue #5
    assert len(pin_set)>0, ValueError("Couldn't find input pin named "+pin_name)
    assert len(pin_set)<2, ValueError("Found more than one input pin named "+pin_name)
    return pin_set[0]
PrimitiveExecutable.input_pin = PrimitiveExecutable_input_pin

def PrimitiveExecutable_output_pin(self, pin_name, doc):
    #pin_set = [x for x in self.output if x.instance_of.lookup().name == pin_name or doc.find(x.instance_of).display_id == pin_name] # note: pySBOL3 issue 229
    pin_set = [x for x in self.output if doc.find(x.instance_of).name == pin_name or doc.find(x.instance_of).display_id == pin_name] # workaround for PAML issue #5
    assert len(pin_set)>0, ValueError("Couldn't find output pin named "+pin_name)
    assert len(pin_set)<2, ValueError("Found more than one output pin named "+pin_name)
    return pin_set[0]
PrimitiveExecutable.output_pin = PrimitiveExecutable_output_pin

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

# Create and add an execution of a primitive to a protocol
def protocol_execute_primitive(self, primitive: Primitive, **input_pin_map):
    pe = make_PrimitiveExecutable(primitive, **input_pin_map)
    self.activities.append(pe)
    return pe
# Monkey patch:
Protocol.execute_primitive = protocol_execute_primitive

# Create and add a flow between the designated child source and sink activities
def protocol_add_flow(self, source, sink):
    assert self.contains_activity(source), ValueError(
        'Source activity ' + source.identity + ' is not a member of protocol ' + self.identity)
    assert self.contains_activity(sink), ValueError(
        'Sink activity ' + sink.identity + ' is not a member of protocol ' + self.identity)
    flow = Flow()
    flow.source = source
    flow.sink = sink
    self.flows.append(flow)
    return flow
# Monkey patch:
Protocol.add_flow = protocol_add_flow


#########################################
# Library handling
current_libraries = {}

def import_library(doc:sbol.Document, library:str, file_format:str = 'ttl' ):
    if not os.path.isfile(library):
        library = posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                 ('lib/'+library+'.ttl'))
    tmp = sbol.Document()
    tmp.read(library, file_format)
    # copy all of the objects into the working document
    for o in tmp.objects: o.copy(doc)
    # TODO: change library imports to copy lazily, using either display_id or lib:display_id to disambiguate
