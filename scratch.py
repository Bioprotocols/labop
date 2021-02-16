import sbol3
import paml
from types import MethodType

def add_input(primitive, name, type, optional=False):
    pin = paml.PinSpecification()
    pin.name = name
    pin.type = type
    pin.optional = optional
    primitive.input += {pin}

def add_output(primitive, name, type):
    pin = paml.PinSpecification()
    pin.name = name
    pin.type = type
    primitive.output += {pin}


# set up the document
doc = paml.Document()

# create the primitives
paml.set_namespace('https://bioprotocols.org/paml/primitives/')

provision = paml.Primitive('Provision')
add_input(provision, 'resource', sbol3.SBOL_COMPONENT)
add_input(provision, 'location', 'http://bioprotocols.org/paml#Location')
add_input(provision, 'volume', sbol3.OM_MEASURE)
add_input(provision, 'dispenseVelosity', sbol3.OM_MEASURE)

measure_absorbance = paml.Primitive('MeasureAbsorbance')
add_input(measure_absorbance, 'location', 'http://bioprotocols.org/paml#Location')
add_output(measure_absorbance, 'measurements', 'http://bioprotocols.org/paml#LocatedData')

# paml.PinSpecification('location')
# paml.PinSpecification('volume')
# paml.PinSpecification('dispenseVelocity')
# paml.PinSpecification('material')

# create the protocol
paml.set_namespace('https://bbn.com/scratch/')
protocol = paml.Protocol('iGEM_LUDOX_OD_calibration_2018')
doc.add(protocol)

# add the initial and final control nodes
initial = paml.Initial()
final = paml.Final()
protocol.hasActivity += {initial, final}

# create the materials to be provisioned

# LUDOX =
ddH2O = sbol3.Component('ddH2O', 'http://identifiers.org/CHEBI:15377')

provision_LUDOX = paml.Activity()
provision_ddH2O = paml.Activity()
protocol.hasActivity += {provision_LUDOX, provision_ddH2O}

#doc.write('scratch.json','json-ld');
print('run complete')
