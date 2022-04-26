import os
import tempfile
import json

import tyto
import sbol3
import rdflib as rdfl

import paml
import uml
from paml.execution_engine import ExecutionEngine
# from paml_check.paml_check import check_doc
from paml_convert.markdown.markdown_specialization import MarkdownSpecialization


#############################################
# set up the document

doc = sbol3.Document()
sbol3.set_namespace('https://bbn.com/scratch/')

#############################################
# Import the primitive libraries
print('Importing libraries')
paml.import_library('liquid_handling')
print('... Imported liquid handling')
paml.import_library('plate_handling')
print('... Imported plate handling')
paml.import_library('spectrophotometry')
print('... Imported spectrophotometry')
paml.import_library('sample_arrays')
print('... Imported sample arrays')
paml.import_library('culturing')

# Display inputs and outputs for each primitive
paml.show_libraries()


protocol = paml.Protocol('HARMONY22')
protocol.name = "HARMONY 2022 Example Cell Calibration protocol"
protocol.description = '''With this protocol you will prepare a standard curve using a fluorescein calibrant and measure the fluorescence of a genetic circuit expressing GFP.'''
doc.add(protocol)

# Create the materials to be provisioned:
# Fluorescein sodium salt, analytical standard
# Water, sterile-filtered, BioReagent, suitable for cell culture: https://identifiers.org/pubchem.substance:24901740
# LB BROTH
# Escherichia coli DH5[Alpha]
# Deoxyribonucleic acid


calibrant = sbol3.Component('fluorescein', tyto.PubChem['Fluorescein sodium salt, analytical standard'])
calibrant.name = 'Fluoroscein'
doc.add(calibrant)

# Declare media, for brevity we will leave out the antibiotic
lb_broth = sbol3.Component('lb_broth', tyto.PubChem['LB BROTH'])
doc.add(lb_broth)

h2o = sbol3.Component('water', 'https://identifiers.org/pubchem.substance:24901740')
doc.add(h2o)

# Declare GFP circuit
test_circuit = sbol3.Component('Test_circuit', tyto.SBO['deoxyribonucleic_acid'])
doc.add(test_circuit)

# Use NCBI taxonomy to declare host strain 
dh5alpha = sbol3.Component('dh5alpha', tyto.NCBITaxon["Escherichia coli DH5[Alpha]"])
dh5alpha.name = 'E. coli DH5alpha'
doc.add(dh5alpha)

# Get a plate and define the sample layout for blanks, standards, and unknown samples
prefix_map = {'cont': rdfl.Namespace('https://sift.net/container-ontology/container-ontology#'),
              'om': rdfl.Namespace('http://www.ontology-of-units-of-measure.org/resource/om-2/')
}

spec = paml.ContainerSpec(name='plate 1', queryString='cont:Well96Plate', prefixMap=json.dumps(prefix_map) )
plate = protocol.primitive_step('EmptyContainer',
                                specification=spec)

# Define target ranges for loading samples
blanks = protocol.primitive_step('PlateCoordinates',
                             source=plate.output_pin('samples'),
                             coordinates='A12:H12')
standards = protocol.primitive_step('PlateCoordinates',
                                source=plate.output_pin('samples'),
                                coordinates='A1:H1')
unknowns = protocol.primitive_step('PlateCoordinates',
                               source=plate.output_pin('samples'),
                               coordinates='A2:H2')

# Transform
# inputs: dna, host, selection_medium
# outputs: transformants
transformation = protocol.primitive_step('Transform',
                                         dna=test_circuit,
                                         host=dh5alpha,
                                         selection_medium=lb_broth)

# Plate blanks  using Provision primitive
# inputs: resource, destination, amount
# output: samples
protocol.primitive_step('Provision',
                        resource=lb_broth,
                        destination=blanks.output_pin('samples'),
                        amount=sbol3.Measure(200, tyto.OM['microliter']))

# Now plate the media for the test circuits. This is left as an exercise.
protocol.primitive_step('Provision',
                        resource=lb_broth,
                        destination=unknowns.output_pin('samples'),
                        amount=sbol3.Measure(200, tyto.OM['microliter']))

# Serial Dilution
# inputs: destination, amount, diluent, dilution_factor, series
# outputs: None
protocol.primitive_step('SerialDilution',
                        source=calibrant,
                        destination=standards.output_pin('samples'),
                        amount=sbol3.Measure(200, tyto.OM['microliter']),
                        dilution_factor=2,
                        diluent=h2o)

protocol.primitive_step('Inoculate',
                        source=transformation.output_pin('transformants'),
                        destination=unknowns.output_pin('samples'))

# Incubate
# inputs: location, duration, temperature
# outputs: None
protocol.primitive_step('Incubate',
                        location=plate.output_pin('samples'),
                        duration=sbol3.Measure(6, tyto.OM['hour']),
                        temperature=sbol3.Measure(37, tyto.OM['degree Celsius']))
                   

# Measure fluorescence
# inputs: samples, excitationWavelength, emissionWavelength
# outputs: measurements
measure_fluorescence = protocol.primitive_step('MeasureFluorescence',
                                                samples=plate.output_pin('samples'))

# Measure absorbance
# inputs: samples, wavelength
# outputs: measurements
measure_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                             samples=plate.output_pin('samples'),
                                             wavelength=sbol3.Measure(600, tyto.OM['nanometer']))

# Configure protocol inputs
ex_wavelength_param = protocol.input_value('excitationWavelength', tyto.OM.Measure)
em_wavelength_param = protocol.input_value('emissionWavelength', tyto.OM.Measure)

protocol.use_value(ex_wavelength_param, measure_fluorescence.input_pin('excitationWavelength'))
protocol.use_value(em_wavelength_param, measure_fluorescence.input_pin('emissionWavelength'))


# Designate protocol outputs for fluorescence and absorbance
protocol.designate_output('fluorescence measurements', tyto.PAML['SampleData'], measure_fluorescence.output_pin('measurements'))
protocol.designate_output('OD600 measurements', tyto.PAML['SampleData'], measure_absorbance.output_pin('measurements'))


# Simulate Execution of the Protocol
agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(specializations=[MarkdownSpecialization(__file__.split('.')[0] + '.md')])
parameter_values = [ paml.ParameterValue(parameter=protocol.get_input('emissionWavelength'),
                                         value=sbol3.Measure(485, tyto.OM['nanometer'])),
                     paml.ParameterValue(parameter=protocol.get_input('excitationWavelength'),
                                         value=sbol3.Measure(510, tyto.OM['nanometer'])),
]
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)
with open(__file__.split('.')[0] + '.md', 'w') as f:
    f.write(ee.specializations[0].markdown)
