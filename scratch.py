import sbol3
import paml
import tyto

#############################################
# Helper functions
def add_input(primitive, name, type, optional="False"):
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

def make_flow(source, sink):
    flow = paml.Flow()
    flow.source = source
    flow.sink = sink
    return flow

def constant_input_pin(executable, pin_spec_name, value):
    pin = paml.LocalValuePin()
    pin.instanceOf = next(x for x in executable.instanceOf.input if x.name==pin_spec_name)
    pin.value = value
    executable.input += {pin}

def make_input_pin(executable, pin_spec_name):
    pin = paml.LocalValuePin()
    pin.instanceOf = next(x for x in executable.instanceOf.input if x.name==pin_spec_name)
    executable.input += {pin}
    return pin

def make_output_pin(executable, pin_spec_name):
    pin = paml.LocalValuePin()
    pin.instanceOf = next(x for x in executable.instanceOf.output if x.name==pin_spec_name)
    executable.output += {pin}
    return pin

# set up the document
doc = paml.Document()


#############################################
# Create the primitives
print('making primitives')

paml.set_namespace('https://bioprotocols.org/paml/primitives/')

provision = paml.Primitive('Provision')
add_input(provision, 'resource', sbol3.SBOL_COMPONENT)
add_input(provision, 'location', 'http://bioprotocols.org/paml#Location')
add_input(provision, 'volume', sbol3.OM_MEASURE)
add_input(provision, 'dispenseVelosity', sbol3.OM_MEASURE, "True")
add_output(provision, 'samples', 'http://bioprotocols.org/paml#LocatedSamples')


measure_absorbance = paml.Primitive('MeasureAbsorbance') # one mode of autoprotocol spectrophotometry
add_input(measure_absorbance, 'location', 'http://bioprotocols.org/paml#LocatedSamples')
add_input(measure_absorbance, 'wavelength', sbol3.OM_MEASURE)
add_output(measure_absorbance, 'measurements', 'http://bioprotocols.org/paml#LocatedData')

#############################################
# Create the protocol
print('making protocol')

paml.set_namespace('https://bbn.com/scratch/')
protocol = paml.Protocol('iGEM_LUDOX_OD_calibration_2018')
doc.add(protocol)

# add the initial and final control nodes
initial = paml.Initial()
final = paml.Final()
protocol.hasActivity += {initial, final}

# create the materials to be provisioned
plate = paml.Container()
plate.type = 'http://identifiers.org/NCIT:C43377' # NCIT microplate
protocol.hasContainer += {plate}

ddH2O = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
ddH2O.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # I'd like to get the names from PubChem with tyto

LUDOX = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
LUDOX.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'

protocol.material += {ddH2O, LUDOX}

# actual steps of the protocol
provision_LUDOX = paml.PrimitiveExecutable()
provision_LUDOX.instanceOf = provision
constant_input_pin(provision_LUDOX, 'resource', LUDOX)
constant_input_pin(provision_LUDOX, 'volume', sbol3.Measure(100, tyto.OM.get_uri_by_term('microliter')))
location = paml.ContainerCoordinates()
location.inContainer = plate
location.coordinates = 'A1:D1'
constant_input_pin(provision_LUDOX, 'location', location)

provision_ddH2O = paml.PrimitiveExecutable()
provision_ddH2O.instanceOf = provision
constant_input_pin(provision_ddH2O, 'resource', ddH2O)
constant_input_pin(provision_ddH2O, 'volume', sbol3.Measure(100, tyto.OM.get_uri_by_term('microliter')))
location = paml.ContainerCoordinates()
location.inContainer = plate
location.coordinates = 'A2:D2'
constant_input_pin(provision_ddH2O, 'location', location)

all_provisioned = paml.Join()
make_flow(make_output_pin(provision_LUDOX, 'samples'), all_provisioned)
make_flow(make_output_pin(provision_ddH2O, 'samples'), all_provisioned)

execute_measurement = paml.PrimitiveExecutable()
execute_measurement.instanceOf = measure_absorbance
constant_input_pin(execute_measurement, 'wavelength', sbol3.Measure(600, tyto.OM.get_uri_by_term('nanometer')))
make_flow(all_provisioned, make_input_pin(execute_measurement, 'location'))

result = paml.Value()
make_flow(make_output_pin(execute_measurement, 'measurements'), result)

make_flow(result, final)

protocol.hasActivity += {provision_LUDOX, provision_ddH2O, all_provisioned, execute_measurement, result}

protocol.output += {result}

print('construction complete')

doc.write('igem_ludox_draft.json','json-ld')
doc.write('igem_ludox_draft.ttl','turtle')

print('writing complete')
