import sbol3
import paml
import tyto

#############################################
# Helper functions

def make_flow(source, sink):
    flow = paml.Flow()
    flow.source = source
    flow.sink = sink
    return flow

# set up the document
doc = sbol3.Document()


#############################################
# Create the primitives
print('making primitives')
sbol3.set_namespace('https://bioprotocols.org/paml/primitives/')

provision = paml.Primitive('Provision')
provision.add_input('resource', sbol3.SBOL_COMPONENT)
provision.add_input('location', 'http://bioprotocols.org/paml#ContainerCoordinates')
provision.add_input('volume', sbol3.OM_MEASURE)
#provision.add_input('dispenseVelosity', sbol3.OM_MEASURE, "True")
provision.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(provision)

measure_absorbance = paml.Primitive('MeasureAbsorbance') # one mode of autoprotocol spectrophotometry
measure_absorbance.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
measure_absorbance.add_input('wavelength', sbol3.OM_MEASURE)
measure_absorbance.add_output('measurements', 'http://bioprotocols.org/paml#LocatedData')
doc.add(measure_absorbance)

#############################################
# Create the protocol
print('making protocol')

sbol3.set_namespace('https://bbn.com/scratch/')
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
protocol.hasActivity.append(initial)
final = paml.Final()
protocol.hasActivity.append(final)

# create the materials to be provisioned
plate = paml.Container()
plate.type = 'http://identifiers.org/NCIT:C43377' # NCIT microplate
plate.name = 'Microplate'
protocol.hasLocation.append(plate)

ddH2O = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
ddH2O.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # I'd like to get the names from PubChem with tyto
doc.add(ddH2O)

LUDOX = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
LUDOX.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
doc.add(LUDOX)

protocol.material += {ddH2O, LUDOX}

samples = paml.LocatedSamples()
protocol.hasLocation.append(samples)

# actual steps of the protocol
location = paml.ContainerCoordinates()
protocol.hasLocation.append(location)
location.inContainer = plate
location.coordinates = 'A1:D1'
provision_LUDOX = paml.PrimitiveExecutable(provision, resource=LUDOX, location=location,
                                           volume=sbol3.Measure(100, tyto.OM.microliter),
                                           samples=samples)
protocol.hasActivity.append(provision_LUDOX)
protocol.hasFlow += {make_flow(initial, provision_LUDOX)}


location = paml.ContainerCoordinates()
protocol.hasLocation.append(location)
location.inContainer = plate
location.coordinates = 'A2:D2'

provision_ddH2O = paml.PrimitiveExecutable(provision, resource=ddH2O, location=location,
                                           volume=sbol3.Measure(100, tyto.OM.microliter),
                                           samples=samples)
protocol.hasActivity.append(provision_ddH2O)
protocol.hasFlow.append(make_flow(initial, provision_ddH2O))


all_provisioned = paml.Join()
samples = sbol3.Collection('samples', name='samples')
protocol.hasActivity.append(all_provisioned)
protocol.hasFlow.append(make_flow(make_output_pin(doc, provision_LUDOX, 'samples'), all_provisioned))
protocol.hasFlow.append(make_flow(make_output_pin(doc, provision_ddH2O, 'samples'), all_provisioned))

execute_measurement = paml.PrimitiveExecutable(measure_absorbance, location=location,
                                               wavelength=sbol3.Measure(600, tyto.OM.nanometer))
protocol.hasActivity.append(execute_measurement)
protocol.hasFlow.append(make_flow(all_provisioned, make_input_pin(doc, execute_measurement, 'location')))

result = paml.Value()
protocol.hasActivity.append(result)
protocol.hasFlow.append(make_flow(make_output_pin(doc, execute_measurement, 'measurements'), result))

protocol.hasFlow.append(make_flow(result, final))

protocol.output += {result}

print('construction complete')

doc.write('igem_ludox_draft.json','json-ld')
doc.write('igem_ludox_draft.ttl','turtle')

print('writing complete')
