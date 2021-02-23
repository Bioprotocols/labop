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

############
# PROBLEM: the instanceOfPin should be a single field, but is coming through as a list!!!
def constant_input_pin(executable, pin_spec_name, value):
    pin = paml.LocalValuePin()
    pin.instanceOfPin = {next(x for x in executable.instanceOf.input if x.name==pin_spec_name)}
    pin.value = value
    executable.input += {pin}

def make_input_pin(executable, pin_spec_name):
    pin = paml.Pin()
    pin.instanceOfPin = {next(x for x in executable.instanceOf.input if x.name==pin_spec_name)}
    executable.input += {pin}
    return pin

def make_output_pin(executable, pin_spec_name):
    pin = paml.Pin()
    pin.instanceOfPin = {next(x for x in executable.instanceOf.output if x.name==pin_spec_name)}
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
protocol.name = "iGEM 2018 LUDOX OD calibration protocol"
protocol.description = '''
With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
'''
doc.add(protocol)

# add the initial and final control nodes
initial = paml.Initial()
final = paml.Final()
protocol.hasActivity += {initial, final}

# create the materials to be provisioned
plate = paml.Container()
plate.type = 'http://identifiers.org/NCIT:C43377' # NCIT microplate
plate.name = 'Microplate'
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
constant_input_pin(provision_LUDOX, 'volume', sbol3.Measure(100, tyto.OM.microliter))
location = paml.ContainerCoordinates()
location.inContainer = plate
location.coordinates = 'A1:D1'
constant_input_pin(provision_LUDOX, 'location', location)
protocol.hasFlow += {make_flow(initial, provision_LUDOX)}

provision_ddH2O = paml.PrimitiveExecutable()
provision_ddH2O.instanceOf = provision
constant_input_pin(provision_ddH2O, 'resource', ddH2O)
constant_input_pin(provision_ddH2O, 'volume', sbol3.Measure(100, tyto.OM.microliter))
location = paml.ContainerCoordinates()
location.inContainer = plate
location.coordinates = 'A2:D2'
constant_input_pin(provision_ddH2O, 'location', location)
protocol.hasFlow += {make_flow(initial, provision_ddH2O)}

all_provisioned = paml.Join()
protocol.hasFlow += {make_flow(make_output_pin(provision_LUDOX, 'samples'), all_provisioned)}
protocol.hasFlow += {make_flow(make_output_pin(provision_ddH2O, 'samples'), all_provisioned)}

execute_measurement = paml.PrimitiveExecutable()
execute_measurement.instanceOf = measure_absorbance
constant_input_pin(execute_measurement, 'wavelength', sbol3.Measure(600, tyto.OM.nanometer))
protocol.hasFlow += {make_flow(all_provisioned, make_input_pin(execute_measurement, 'location'))}

result = paml.Value()
protocol.hasFlow += {make_flow(make_output_pin(execute_measurement, 'measurements'), result)}

protocol.hasFlow += {make_flow(result, final)}

protocol.hasActivity += {provision_LUDOX, provision_ddH2O, all_provisioned, execute_measurement, result}

protocol.output += {result}

print('construction complete')

doc.write('igem_ludox_draft.json','json-ld')
doc.write('igem_ludox_draft.ttl','turtle')

print('writing complete')
