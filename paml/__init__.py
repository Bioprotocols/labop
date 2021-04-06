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
def add_input(self, name, type, optional="False"):
    pin = PinSpecification()
    pin.name = name
    pin.type = type
    pin.optional = optional
    self.input.append(pin)

def add_output(self, name, type):
    pin = PinSpecification()
    pin.name = name
    pin.type = type
    self.output.append(pin)

# Monkey patch
Primitive.add_input = add_input
Primitive.add_output = add_output

# Alias PrimitiveExecutable because we are going to supplant it
PrimitiveExecutableBase = PrimitiveExecutable

class PrimitiveExecutable(PrimitiveExecutableBase):

    def __init__(self, primitive: PrimitiveExecutableBase, **pin_map):
        PrimitiveExecutableBase.__init__(self)       

        # Validate keyword arguments, one Pin value for every PinSpec
        for p in primitive.input:
            if p.name not in pin_map:
                raise ValueError(f'{primitive.name} requires a {p.name} input Pin')
        for p in primitive.output:
            if p.name not in pin_map:
                raise ValueError(f'{primitive.name} requires a {p.name} output Pin')

        # Instantiate input pins
        for pin_spec in primitive.input:
            val = pin_map[pin_spec.name]
            if val.type_uri != pin_spec.type:
                raise TypeError(f'{pin_spec.name} must be of type {pin_spec.type}')

            # Construct Pin of appropriate subtype
            if isinstance(val, sbol.TopLevel):
                pin = ReferenceValuePin()
            elif type(val) is sbol.Measure:
                pin = LocalValuePin()
            else:
                pin = Pin()

            # Set properties
            pin.name = pin_spec.name
            pin.instanceOf = pin_spec
            pin_spec.value = val
            self.input.append(pin)

        # Instantiate output pins
        for pin_spec in primitive.output:
            val = pin_map[pin_spec.name]
            if val.type_uri != pin_spec.type:
                raise TypeError(f'{pin_spec.name} must be of type {pin_spec.type}')

            # Construct Pin of appropriate subtype
            if isinstance(val, sbol.TopLevel):
                pin = ReferenceValuePin()
            elif type(val) is sbol.Measure:
                pin = LocalValuePin()
            else:
                pin = Pin()
            
            # Set properties
            pin.name = pin_spec.name
            pin.instanceOf = pin_spec
            pin_spec.value = val
            self.output.append(pin)
        
        # Add new instance to Document
        #primitive.document.add(self)

    def get_pin(self, pin_id):

########################
# Another helper; this one should probably be added as an extension

# Alias Protocol because we are going to supplant it
ProtocolBase = Protocol

class Protocol(ProtocolBase):

    # Create and add a flow between the designated child source and sink activities
    def add_flow(self, source, sink):
        assert source in self.hasActivity, ValueError('Source activity '+print(source.identity)+' is not a member of protocol '+print(self.identity))
        assert sink in self.hasActivity, ValueError('Sink activity '+print(sink.identity)+' is not a member of protocol '+print(self.identity))
        flow = Flow()
        flow.source = source
        flow.sink = sink
        self.hasFlow.append(flow)
        return flow



def import_library(doc:sbol.Document, location:str, file_format:str = None ):
    tmp = sbol.Document()
    tmp.read(location, file_format)
    # copy all of the objects into the working document
    for o in tmp.objects: o.copy(doc)
