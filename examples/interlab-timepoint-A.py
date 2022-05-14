'''
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
'''
import json
from urllib.parse import quote

import sbol3
from tyto import OM

import paml
import uml
from paml.execution_engine import ExecutionEngine
from paml_convert.markdown.markdown_specialization import MarkdownSpecialization


doc = sbol3.Document()
sbol3.set_namespace('http://igem.org/engineering/')

#############################################
# Import the primitive libraries
print('Importing libraries')
paml.import_library('liquid_handling')
print('... Imported liquid handling')
paml.import_library('plate_handling')
# print('... Imported plate handling')
paml.import_library('spectrophotometry')
print('... Imported spectrophotometry')
paml.import_library('sample_arrays')
print('... Imported sample arrays')
paml.import_library('culturing')
#############################################


# create the materials to be provisioned
dh5alpha = sbol3.Component('dh5alpha', 'https://identifiers.org/pubchem.substance:24901740')
dh5alpha.name = '_E. coli_ DH5 alpha'  
doc.add(dh5alpha)

lb_cam = sbol3.Component('lb_cam', 'https://identifiers.org/pubchem.substance:24901740')
lb_cam.name = 'LB Broth+chloramphenicol'  
doc.add(lb_cam)

chloramphenicol = sbol3.Component('chloramphenicol', 'https://identifiers.org/pubchem.substance:24901740')
chloramphenicol.name = 'chloramphenicol'  
doc.add(chloramphenicol)


neg_control_plasmid = sbol3.Component('neg_control_plasmid', sbol3.SBO_DNA)
neg_control_plasmid.name = 'Negative control'
neg_control_plasmid.description = 'BBa_R0040 Kit Plate 7 Well 2D'

pos_control_plasmid = sbol3.Component('pos_control_plasmid', sbol3.SBO_DNA)
pos_control_plasmid.name = 'Positive control'
pos_control_plasmid.description = 'BBa_I20270 Kit Plate 7 Well 2B'

test_device1 = sbol3.Component('test_device1', sbol3.SBO_DNA)
test_device1.name = 'Test Device 1'
test_device1.description = 'BBa_J364000 Kit Plate 7 Well 2F'

test_device2 = sbol3.Component('test_device2', sbol3.SBO_DNA)
test_device2.name = 'Test Device 2'
test_device2.description = 'BBa_J364001 Kit Plate 7 Well 2H'

test_device3 = sbol3.Component('test_device3', sbol3.SBO_DNA)
test_device3.name = 'Test Device 3'
test_device3.description = 'BBa_J364002 Kit Plate 7 Well 2J'

test_device4 = sbol3.Component('test_device4', sbol3.SBO_DNA)
test_device4.name = 'Test Device 4'
test_device4.description = 'BBa_J364007 Kit Plate 7 Well 2L'

test_device5 = sbol3.Component('test_device5', sbol3.SBO_DNA)
test_device5.name = 'Test Device 5'
test_device5.description = 'BBa_J364008 Kit Plate 7 Well 2N'

test_device6 = sbol3.Component('test_device6', sbol3.SBO_DNA)
test_device6.name = 'Test Device 6'
test_device6.description = 'BBa_J364009 Kit Plate 7 Well 2P'

doc.add(neg_control_plasmid)
doc.add(pos_control_plasmid)
doc.add(test_device1)
doc.add(test_device2)
doc.add(test_device3)
doc.add(test_device4)
doc.add(test_device5)
doc.add(test_device6)


protocol = paml.Protocol('interlab')
protocol.name = 'Cell measurement protocol'
protocol.version = sbol3.TextProperty(protocol, 'http://igem.org/interlab_working_group#Version', 0, 1, [], '1.0b')
protocol.description = '''Challenging A - This version of the protocol involves 2 hr. time-point measurements using a plate-reader, but incubation may be performed inside a bench-top or standing incubator. 

Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.'''

doc.add(protocol)
protocol = doc.find(protocol.identity)

plasmids = [neg_control_plasmid, pos_control_plasmid, test_device1, test_device2, test_device3, test_device4, test_device5, test_device6]

# Day 1: Transformation
transformation = protocol.primitive_step(f'Transform',
                                          host=dh5alpha,
                                          dna=plasmids,
                                          selection_medium=lb_cam)
    
# Day 2: Pick colonies and culture overnight
culture_container_day1 = protocol.primitive_step('ContainerSet', 
                                                 quantity=2*len(plasmids),
                                                 specification=paml.ContainerSpec(name=f'culture (day 1)',
                                                                                  queryString='cont:CultureTube', 
                                                                                  prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

overnight_culture = protocol.primitive_step('Culture',
                                            inoculum=transformation.output_pin('transformants'),
                                            replicates=2,
                                            growth_medium=lb_cam,
                                            volume=sbol3.Measure(5, OM.millilitre),  # Actually 5-10 ml in the written protocol
                                            duration=sbol3.Measure(16, OM.hour), # Actually 16-18 hours
                                            orbital_shake_speed=sbol3.Measure(220, None),  # No unit for RPM or inverse minutes
                                            temperature=sbol3.Measure(37, OM.degree_Celsius),
                                            container=culture_container_day1.output_pin('samples'))

# Day 3 culture
culture_container_day2 = protocol.primitive_step('ContainerSet',
                                                  quantity=2*len(plasmids), 
                                                  specification=paml.ContainerSpec(name=f'culture (day 2)',
                                                                                   queryString='cont:CultureTube', 
                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))



back_dilution = protocol.primitive_step('Dilute',
                                        source=culture_container_day1.output_pin('samples'),
                                        destination=culture_container_day2.output_pin('samples'),
                                        replicates=2,
                                        diluent=lb_cam,
                                        amount=sbol3.Measure(10.0, OM.millilitre),
                                        dilution_factor=uml.LiteralInteger(value=10),
                                        temperature=sbol3.Measure(4, OM.degree_Celsius))

# Transfer cultures to a microplate baseline measurement and outgrowth
timepoint_0hrs = protocol.primitive_step('ContainerSet',
                                         quantity=2*len(plasmids), 
                                         specification=paml.ContainerSpec(name='cultures (0 hr timepoint)',
                                         queryString='cont:MicrofugeTube',
                                         prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

hold = protocol.primitive_step('Hold',
                               location=timepoint_0hrs.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))
hold.description = 'This will prevent cell growth while transferring samples.'

transfer = protocol.primitive_step('Transfer',
                                   source=culture_container_day2.output_pin('samples'),
                                   destination=timepoint_0hrs.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))

baseline_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                              samples=timepoint_0hrs.output_pin('samples'),
                                              wavelength=sbol3.Measure(600, OM.nanometer))
baseline_absorbance.name = 'baseline absorbance of culture (day 2)'

protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=baseline_absorbance.output_pin('measurements'))


conical_tube = protocol.primitive_step('ContainerSet', 
                                       quantity=2*len(plasmids),
                                       specification=paml.ContainerSpec(name=f'back-diluted culture',
                                       queryString='cont:50mlConicalTube',
                                       prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'})) 
conical_tube.description = 'The conical tube should be opaque, amber-colored, or covered with foil.'

dilution = protocol.primitive_step('DiluteToTargetOD',
                                   source=culture_container_day2.output_pin('samples'),
                                   destination=conical_tube.output_pin('samples'),
                                   diluent=lb_cam,
                                   amount=sbol3.Measure(40, OM.millilitre),
                                   target_od=sbol3.Measure(0.02, None),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))  # Dilute to a target OD of 0.2, opaque container
dilution.description = ' Use the provided Excel sheet to calculate this dilution. Reliability of the dilution upon Abs600 measurement: should stay between 0.1-0.9'

embedded_image = protocol.primitive_step('EmbeddedImage',
                                         image='/Users/bbartley/Dev/git/sd2/paml/fig1_cell_calibration.png')


### Aliquot subcultures for timepoint samples

timepoint_subculture1 = protocol.primitive_step('ContainerSet', 
                                           quantity=2*len(plasmids),
                                           specification=paml.ContainerSpec(name=f'Tube 1',
                                           queryString='cont:50mlConicalTube',
                                           prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'})) 
timepoint_subculture1.description = 'The conical tubes should be opaque, amber-colored, or covered with foil.'

timepoint_subculture2 = protocol.primitive_step('ContainerSet', 
                                           quantity=2*len(plasmids),
                                           specification=paml.ContainerSpec(name=f'Tube 2',
                                           queryString='cont:50mlConicalTube',
                                           prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'})) 
timepoint_subculture2.description = 'The conical tubes should be opaque, amber-colored, or covered with foil.'

timepoint_subculture3 = protocol.primitive_step('ContainerSet', 
                                           quantity=2*len(plasmids),
                                           specification=paml.ContainerSpec(name=f'Tube 3',
                                           queryString='cont:50mlConicalTube',
                                           prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'})) 
timepoint_subculture3.description = 'The conical tubes should be opaque, amber-colored, or covered with foil.'

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tube.output_pin('samples'),
                                   destination=timepoint_subculture1.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tube.output_pin('samples'),
                                   destination=timepoint_subculture2.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tube.output_pin('samples'),
                                   destination=timepoint_subculture3.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))

plate1 = protocol.primitive_step('EmptyContainer',
                                 specification=paml.ContainerSpec(name='plate 1',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
plate2 = protocol.primitive_step('EmptyContainer',
                                 specification=paml.ContainerSpec(name='plate 2',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
plate3 = protocol.primitive_step('EmptyContainer',
                                 specification=paml.ContainerSpec(name='plate 3',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))


hold = protocol.primitive_step('Hold',
                               location=plate1.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))

map = quote(json.dumps({'1':  'A2:D2',
                                                '2':  'E2:H2',
                                                '3':  'A3:D3',
                                                '4':  'E3:H3',
                                                '5':  'A4:D4',
                                                '6':  'E4:H4',
                                                '7':  'A5:D5',
                                                '8':  'E5:H5',
                                                '9':  'A7:D7',
                                                '10': 'E7:H7',
                                                '11': 'A8:D8',
                                                '12': 'E8:H8',
                                                '13': 'A9:D9',
                                                '14': 'E9:H9',
                                                '15': 'A10:D10',
                                                '16': 'E10:H10',}))

plan = paml.SampleData(values=map)
transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_subculture1.output_pin('samples'),
                                    destination=plate1.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    temperature=sbol3.Measure(4, OM.degree_Celsius),
                                    plan=plan)
transfer.description = 'See the plate layout below.'
plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate1.output_pin('samples'),
                                       coordinates='A1:H1, A10:H10, A12:H12',
                                       temperature=sbol3.Measure(4, OM.degree_Celsius),
                                       amount=sbol3.Measure(100, OM.microliter))
plate_blanks.description = 'These samples are blanks.'


plan = paml.SampleData(values=map)
transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_subculture2.output_pin('samples'),
                                    destination=plate2.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    temperature=sbol3.Measure(4, OM.degree_Celsius),
                                    plan=plan)
transfer.description = 'See the plate layout below.'

plan = paml.SampleData(values=map)
plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate2.output_pin('samples'),
                                       coordinates='A1:H1, A10:H10, A12:H12',
                                       temperature=sbol3.Measure(4, OM.degree_Celsius),
                                       amount=sbol3.Measure(100, OM.microliter))
plate_blanks.description = 'These samples are blanks.'

plan = paml.SampleData(values=map)
transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_subculture3.output_pin('samples'),
                                    destination=plate3.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    temperature=sbol3.Measure(4, OM.degree_Celsius),
                                    plan=plan)
transfer.description = 'See the plate layout below.'

plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate1.output_pin('samples'),
                                       coordinates='A1:H1, A10:H10, A12:H12',
                                       temperature=sbol3.Measure(4, OM.degree_Celsius),
                                       amount=sbol3.Measure(100, OM.microliter))
plate_blanks.description = 'These samples are blanks.'


embedded_image = protocol.primitive_step('EmbeddedImage',
                                         image='/Users/bbartley/Dev/git/sd2/paml/fig2_cell_calibration.png')

# Cover plate
seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate1.output_pin('samples'),
                               type='foo')

seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate2.output_pin('samples'),
                               type='foo')
seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate3.output_pin('samples'),
                               type='foo')

# Possibly display map here
absorbance_plate1 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate1.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_plate1.name = '0 hr absorbance timepoint'
absorbance_plate2 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate1.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_plate2.name = '0 hr absorbance timepoint'
absorbance_plate3 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate1.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_plate3.name = '0 hr absorbance timepoint'

fluorescence_plate1 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate1.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_plate1.name = '0 hr fluorescence timepoint'
fluorescence_plate2 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate1.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_plate2.name = '0 hr fluorescence timepoint'
fluorescence_plate3 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate1.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_plate3.name = '0 hr fluorescence timepoint'

protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=absorbance_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=fluorescence_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=absorbance_plate2.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=fluorescence_plate2.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=absorbance_plate3.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=fluorescence_plate3.output_pin('measurements'))


# Begin outgrowth
incubate = protocol.primitive_step('Incubate',
                                   location=timepoint_subculture1.output_pin('samples'),
                                   duration=sbol3.Measure(2, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

incubate = protocol.primitive_step('Incubate',
                                   location=plate1.output_pin('samples'),
                                   duration=sbol3.Measure(2, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

incubate = protocol.primitive_step('Incubate',
                                   location=timepoint_subculture2.output_pin('samples'),
                                   duration=sbol3.Measure(4, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

incubate = protocol.primitive_step('Incubate',
                                   location=plate2.output_pin('samples'),
                                   duration=sbol3.Measure(4, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))
incubate = protocol.primitive_step('Incubate',
                                   location=timepoint_subculture3.output_pin('samples'),
                                   duration=sbol3.Measure(6, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

incubate = protocol.primitive_step('Incubate',
                                   location=plate3.output_pin('samples'),
                                   duration=sbol3.Measure(6, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))



def timepoint_measurement(timepoint, timepoint_subculture, plate, temporary_plate_name):
    
    # Hold on ice to inhibit cell growth
    hold = protocol.primitive_step('Hold',
                                   location=timepoint_subculture.output_pin('samples'),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))
    hold.description = 'This will inhibit cell growth during the subsequent pipetting steps.'
    
    hold = protocol.primitive_step('Hold',
                                   location=plate.output_pin('samples'),
                                   temperature=sbol3.Measure(4, OM.degree_Celsius))
    hold.description = 'This will inhibit cell growth during the subsequent pipetting steps.'
    
    
    # Take a 2hr timepoint measurement
    temporary_plate = protocol.primitive_step('EmptyContainer',
                                     specification=paml.ContainerSpec(name=temporary_plate_name,
                                     queryString='cont:Plate96Well',
                                     prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
    
    plan = paml.SampleData(values=map)
    transfer = protocol.primitive_step('TransferByMap',
                                        source=timepoint_subculture.output_pin('samples'),
                                        destination=temporary_plate.output_pin('samples'),
                                        amount=sbol3.Measure(100, OM.microliter),
                                        temperature=sbol3.Measure(4, OM.degree_Celsius),
                                        plan=plan)
    transfer.description = 'See the plate layout below.'
    plate_blanks = protocol.primitive_step('Transfer',
                                           source=[lb_cam],
                                           destination=temporary_plate.output_pin('samples'),
                                           coordinates='A1:H1, A10:H10, A12:H12',
                                           temperature=sbol3.Measure(4, OM.degree_Celsius),
                                           amount=sbol3.Measure(100, OM.microliter))
    plate_blanks.description = 'These samples are blanks.'
    
    absorbance_plate = protocol.primitive_step('MeasureAbsorbance',
                                                    samples=plate.output_pin('samples'),
                                                    wavelength=sbol3.Measure(600, OM.nanometer))
    absorbance_plate.name = f'{timepoint} absorbance timepoint'
    fluorescence_plate = protocol.primitive_step('MeasureFluorescence',
                                                      samples=plate.output_pin('samples'),
                                                      excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                                      emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                      emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
    fluorescence_plate.name = f'{timepoint} fluorescence timepoint'
    protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=absorbance_plate.output_pin('measurements'))
    protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=fluorescence_plate.output_pin('measurements'))

    
    absorbance_plate = protocol.primitive_step('MeasureAbsorbance',
                                                    samples=temporary_plate.output_pin('samples'),
                                                    wavelength=sbol3.Measure(600, OM.nanometer))
    absorbance_plate.name = f'{timepoint} absorbance timepoint'
    fluorescence_plate = protocol.primitive_step('MeasureFluorescence',
                                                      samples=temporary_plate.output_pin('samples'),
                                                      excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                                      emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                      emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
    fluorescence_plate.name = f'{timepoint} fluorescence timepoint'
    protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=absorbance_plate.output_pin('measurements'))
    protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=fluorescence_plate.output_pin('measurements'))

timepoint_measurement('2 hr', timepoint_subculture1, plate1, 'plate4')
timepoint_measurement('4 hr', timepoint_subculture2, plate2, 'plate5')
timepoint_measurement('6 hr', timepoint_subculture3, plate3, 'plate6')




agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=[])
print(ee.specializations[0].markdown)
ee.specializations[0].markdown = ee.specializations[0].markdown.replace('`_E. coli_', '_`E. coli`_ `')
with open(__file__.split('.')[0] + '.md', 'w', encoding='utf-8') as f:
    f.write(ee.specializations[0].markdown)
