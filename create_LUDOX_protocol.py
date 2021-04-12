import sbol3
import paml
import tyto

#############################################
# Helper functions

# set up the document
doc = sbol3.Document()
sbol3.set_namespace('https://bbn.com/scratch/')

#############################################
# Import the primitive libraries
print('Importing libraries')
paml.import_library(doc, 'lib/liquid_handling.ttl','ttl')
paml.import_library(doc, 'lib/plate_handling.ttl','ttl')
paml.import_library(doc, 'lib/spectrophotometry.ttl','ttl')


#############################################
# Create the protocol
print('Making protocol')

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
plate = paml.Container(name='Microplate', type=tyto.NCIT.get_uri_by_term('Microplate'))
protocol.hasLocation.append(plate)

ddH2O = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
ddH2O.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # I'd like to get the names from PubChem with tyto
doc.add(ddH2O)

LUDOX = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
LUDOX.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
doc.add(LUDOX)

protocol.material += {ddH2O, LUDOX}

# actual steps of the protocol
location = paml.ContainerCoordinates()
protocol.hasLocation.append(location)
location.inContainer = plate
location.coordinates = 'A1:D1'
provision_LUDOX = paml.make_PrimitiveExecutable(doc.find('Provision'), resource=LUDOX, destination=location,
                                           amount=sbol3.Measure(100, tyto.OM.microliter))
protocol.hasActivity.append(provision_LUDOX)
protocol.add_flow(initial, provision_LUDOX)


location = paml.ContainerCoordinates()
protocol.hasLocation.append(location)
location.inContainer = plate
location.coordinates = 'A2:D2'
provision_ddH2O = paml.make_PrimitiveExecutable(doc.find('Provision'), resource=ddH2O, destination=location,
                                           amount=sbol3.Measure(100, tyto.OM.microliter))
protocol.hasActivity.append(provision_ddH2O)
protocol.add_flow(initial, provision_ddH2O)


all_provisioned = paml.Join()
protocol.hasActivity.append(all_provisioned)
protocol.add_flow(provision_LUDOX.output_pin('samples',doc), all_provisioned)
protocol.add_flow(provision_ddH2O.output_pin('samples',doc), all_provisioned)

execute_measurement = paml.make_PrimitiveExecutable(doc.find('MeasureAbsorbance'),
                                               wavelength=sbol3.Measure(600, tyto.OM.nanometer))
protocol.hasActivity.append(execute_measurement)
protocol.add_flow(all_provisioned, execute_measurement.input_pin('samples',doc))

result = paml.Value()
protocol.hasActivity.append(result)
protocol.add_flow(execute_measurement.output_pin('measurements',doc), result)

protocol.add_flow(result, final)

protocol.output += {result}

print('Protocol construction complete')

print('Validating document')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

print('Writing document')

doc.write('igem_ludox_draft.json','json-ld')
doc.write('igem_ludox_draft.ttl','turtle')

print('Complete')
