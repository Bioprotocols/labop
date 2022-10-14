'''
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
'''
import json
from urllib.parse import quote

import sbol3
from tyto import OM

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization


doc = sbol3.Document()
sbol3.set_namespace('http://igem.org/engineering/')

#############################################
# Import the primitive libraries
print('Importing libraries')
labop.import_library('liquid_handling')
print('... Imported liquid handling')
labop.import_library('plate_handling')
# print('... Imported plate handling')
labop.import_library('spectrophotometry')
print('... Imported spectrophotometry')
labop.import_library('sample_arrays')
print('... Imported sample arrays')
labop.import_library('culturing')
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


protocol = labop.Protocol('interlab')
protocol.name = 'Cell measurement protocol (Challenging)'
protocol.description = '''
This is a more challenging version of the cell calibration protocol for time-interval measurement. At each time point 0-hour, 2-hour, 4-hour and 6-hour, you will take a sample from each of the eight devices, two colonies per device, three falcon tubes per colony → total 48 tubes.'''
protocol.version = '1.0b'
doc.add(protocol)

plasmids = [neg_control_plasmid, pos_control_plasmid, test_device1, test_device2, test_device3, test_device4, test_device5, test_device6]

# Day 1: Transformation
transformation = protocol.primitive_step(f'Transform',
                                          host=dh5alpha,
                                          dna=plasmids,
                                          selection_medium=lb_cam)

# Day 2: Pick colonies and culture overnight
culture_container_day1 = protocol.primitive_step('ContainerSet',
                                                 quantity=2*len(plasmids),
                                                 specification=labop.ContainerSpec(name=f'culture (day 1)',
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
                                                  specification=labop.ContainerSpec(name=f'culture (day 2)',
                                                                                   queryString='cont:CultureTube',
                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))



back_dilution = protocol.primitive_step('Dilute',
                                        source=culture_container_day1.output_pin('samples'),
                                        destination=culture_container_day2.output_pin('samples'),
                                        replicates=2,
                                        diluent=lb_cam,
                                        amount=sbol3.Measure(5.0, OM.millilitre),
                                        dilution_factor=uml.LiteralInteger(value=10))

baseline_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                              samples=culture_container_day2.output_pin('samples'),
                                              wavelength=sbol3.Measure(600, OM.nanometer))
baseline_absorbance.name = 'baseline absorbance'

parent_conical_tube = protocol.primitive_step('ContainerSet',
                                              quantity=2*len(plasmids),
                                              specification=labop.ContainerSpec(name=f'back-diluted culture',
                                              queryString='cont:50mlConicalTube',
                                              prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

dilution = protocol.primitive_step('DiluteToTargetOD',
                                   source=culture_container_day2.output_pin('samples'),
                                   destination=parent_conical_tube.output_pin('samples'),
                                   diluent=lb_cam,
                                   amount=sbol3.Measure(40, OM.millilitre),
                                   target_od=sbol3.Measure(0.2, None))  # Dilute to a target OD of 0.2, opaque container
dilution.description = '(Reliability of the dilution upon Abs600 measurement: should stay between 0.1-0.9)'

# Further subdivision into triplicates
conical_tubes = protocol.primitive_step('ContainerSet',
                                       quantity=2*len(plasmids),
                                       replicates=3,
                                       specification=labop.ContainerSpec(name=f'replicate subcultures',
                                       queryString='cont:50mlConicalTube',
                                       prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
conical_tubes.description = 'The conical tubes should be opaque, amber-colored, or covered with foil.'

transfer = protocol.primitive_step('Transfer',
                                   source=parent_conical_tube.output_pin('samples'),
                                   replicates=3,
                                   destination=conical_tubes.output_pin('samples'),
                                   amount=sbol3.Measure(12, OM.milliliter))

embedded_image = protocol.primitive_step('EmbeddedImage',
                                         image='/Users/bbartley/Dev/git/sd2/labop/fig3_cell_calibration.png')


# Transfer cultures to a microplate baseline measurement and outgrowth
timepoint_0hrs = protocol.primitive_step('ContainerSet',
                                         quantity=2*len(plasmids)*3,
                                         specification=labop.ContainerSpec(name='cultures (0 hr timepoint)',
                                         queryString='cont:MicrofugeTube',
                                         prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
# Hold on ice
hold = protocol.primitive_step('Hold',
                               location=timepoint_0hrs.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))
hold.description = 'This will prevent cell growth while transferring samples.'

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tubes.output_pin('samples'),
                                   destination=timepoint_0hrs.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter))

# Plate cultures
plate1 = protocol.primitive_step('EmptyContainer',
                                 specification=labop.ContainerSpec(name='plate 1',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
plate2 = protocol.primitive_step('EmptyContainer',
                                 specification=labop.ContainerSpec(name='plate 2',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
plate3 = protocol.primitive_step('EmptyContainer',
                                 specification=labop.ContainerSpec(name='plate 3',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))


hold = protocol.primitive_step('Hold',
                               location=plate1.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))

hold = protocol.primitive_step('Hold',
                               location=plate2.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))

hold = protocol.primitive_step('Hold',
                               location=plate3.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))


transfer_map = quote(json.dumps({'1':  'A2:D2',
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
                                                '16': 'E10:H10',
                                                '17':  'A2:D2',
                                                '18':  'E2:H2',
                                                '19':  'A3:D3',
                                                '20':  'E3:H3',
                                                '21':  'A4:D4',
                                                '22':  'E4:H4',
                                                '23':  'A5:D5',
                                                '24':  'E5:H5',
                                                '25':  'A7:D7',
                                                '26': 'E7:H7',
                                                '27': 'A8:D8',
                                                '28': 'E8:H8',
                                                '29': 'A9:D9',
                                                '30': 'E9:H9',
                                                '31': 'A10:D10',
                                                '32': 'E10:H10',
                                                '33':  'A2:D2',
                                                '34':  'E2:H2',
                                                '35':  'A3:D3',
                                                '36':  'E3:H3',
                                                '37':  'A4:D4',
                                                '38':  'E4:H4',
                                                '39':  'A5:D5',
                                                '40':  'E5:H5',
                                                '41':  'A7:D7',
                                                '42': 'E7:H7',
                                                '43': 'A8:D8',
                                                '44': 'E8:H8',
                                                '45': 'A9:D9',
                                                '46': 'E9:H9',
                                                '47': 'A10:D10',
                                                '48': 'E10:H10',}))


plan = labop.SampleData(values=transfer_map)
transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_0hrs.output_pin('samples'),
                                    destination=plate1.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    plan=plan)
transfer.description = 'See the plate layout below.'

plan = labop.SampleData(values=transfer_map)

transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_0hrs.output_pin('samples'),
                                    destination=plate2.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    plan=plan)
plan = labop.SampleData(values=transfer_map)

transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_0hrs.output_pin('samples'),
                                    destination=plate3.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    plan=plan)




plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate1.output_pin('samples'),
                                       coordinates='A1:H1, A10:H10, A12:H12',
                                       amount=sbol3.Measure(100, OM.microliter))
plate_blanks.description = 'These samples are blanks.'

embedded_image = protocol.primitive_step('EmbeddedImage',
                                         image='/Users/bbartley/Dev/git/sd2/labop/fig2_cell_calibration.png')



# Possibly display map here
absorbance_0hrs_plate1 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate1.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_0hrs_plate1.name = '0 hr absorbance timepoint'

fluorescence_0hrs_plate1 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate1.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_0hrs_plate1.name = '0 hr fluorescence timepoint'

absorbance_0hrs_plate2 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate2.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_0hrs_plate2.name = '0 hr absorbance timepoint'
fluorescence_0hrs_plate2 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate2.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_0hrs_plate2.name = '0 hr fluorescence timepoint'

absorbance_0hrs_plate3 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate3.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_0hrs_plate3.name = '0 hr absorbance timepoint'
fluorescence_0hrs_plate3 = protocol.primitive_step('MeasureFluorescence',
                                                  samples=plate3.output_pin('samples'),
                                                  excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                                  emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                  emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_0hrs_plate3.name = '0 hr fluorescence timepoint'

## Cover plate
seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate1.output_pin('samples'),
                               type='foo')
seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate2.output_pin('samples'),
                               type='foo')
seal = protocol.primitive_step('EvaporativeSeal',
                               location=plate3.output_pin('samples'),
                               type='foo')



## Begin outgrowth
incubate = protocol.primitive_step('Incubate',
                                   location=conical_tubes.output_pin('samples'),
                                   duration=sbol3.Measure(2, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

incubate = protocol.primitive_step('Incubate',
                                   location=plate1.output_pin('samples'),
                                   duration=sbol3.Measure(2, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))
incubate = protocol.primitive_step('Incubate',
                                   location=plate2.output_pin('samples'),
                                   duration=sbol3.Measure(4, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))
incubate = protocol.primitive_step('Incubate',
                                   location=plate1.output_pin('samples'),
                                   duration=sbol3.Measure(6, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

# Hold on ice to inhibit cell growth
hold = protocol.primitive_step('Hold',
                               location=conical_tubes.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))
hold.description = 'This will inhibit cell growth during the subsequent pipetting steps.'

hold = protocol.primitive_step('Hold',
                               location=plate1.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))
hold.description = 'This will inhibit cell growth during the subsequent pipetting steps.'

# Transfer cultures to a microplate baseline measurement and outgrowth
timepoint_2hrs = protocol.primitive_step('ContainerSet',
                                         quantity=2*len(plasmids)*3,
                                         specification=labop.ContainerSpec(name='cultures (0 hr timepoint)',
                                         queryString='cont:MicrofugeTube',
                                         prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

# Hold on ice
hold = protocol.primitive_step('Hold',
                               location=timepoint_2hrs.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))
hold.description = 'This will prevent cell growth while transferring samples.'

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tubes.output_pin('samples'),
                                   destination=timepoint_2hrs.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.milliliter))

plate4 = protocol.primitive_step('EmptyContainer',
                                 specification=labop.ContainerSpec(name='plate 4',
                                 queryString='cont:Plate96Well',
                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

plan = labop.SampleData(values=transfer_map)
transfer = protocol.primitive_step('TransferByMap',
                                    source=timepoint_2hrs.output_pin('samples'),
                                    destination=plate4.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    plan=plan)
# Plate the blanks
plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate4.output_pin('samples'),
                                       coordinates='A1:H1, A10:H10, A12:H12',
                                       amount=sbol3.Measure(100, OM.microliter))
plate_blanks.description = 'These are the blanks.'


quick_spin = protocol.primitive_step('QuickSpin',
                                     location=plate1.output_pin('samples'))
quick_spin.description = 'This will prevent cross-contamination when removing the seal.'

remove_seal = protocol.primitive_step('Unseal',
                                      location=plate1.output_pin('samples'))

absorbance_2hrs_plate1 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate1.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_2hrs_plate1.name = '2 hr absorbance timepoint'
fluorescence_2hrs_plate1 = protocol.primitive_step('MeasureFluorescence',
                                                       samples=plate1.output_pin('samples'),
                                                       excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                                       emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                       emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_2hrs_plate1.name = '2 hr fluorescence timepoint'

absorbance_2hrs_plate4 = protocol.primitive_step('MeasureAbsorbance',
                                                samples=plate4.output_pin('samples'),
                                                wavelength=sbol3.Measure(600, OM.nanometer))
absorbance_2hrs_plate4.name = '2 hr absorbance timepoint'
fluorescence_2hrs_plate4 = protocol.primitive_step('MeasureFluorescence',
                                                       samples=plate4.output_pin('samples'),
                                                       excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                                       emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                                       emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
fluorescence_2hrs_plate4.name = '2 hr fluorescence timepoint'

#endpoint_fluorescence_plate1 = protocol.primitive_step('MeasureFluorescence',
#                                                       samples=plate4.output_pin('samples'),
#                                                       excitationWavelength=sbol3.Measure(485, OM.nanometer),
#                                                       emissionWavelength=sbol3.Measure(530, OM.nanometer),
#                                                       emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
#
#endpoint_absorbance_plate2 = protocol.primitive_step('MeasureAbsorbance',
#                                                     samples=plate2.output_pin('samples'),
#                                                     wavelength=sbol3.Measure(600, OM.nanometer))
#
#endpoint_fluorescence_plate2 = protocol.primitive_step('MeasureFluorescence',
#                                                       samples=plate2.output_pin('samples'),
#                                                       excitationWavelength=sbol3.Measure(485, OM.nanometer),
#                                                       emissionWavelength=sbol3.Measure(530, OM.nanometer),
#                                                       emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
#
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=baseline_absorbance.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_0hrs_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_0hrs_plate2.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_0hrs_plate3.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_0hrs_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_0hrs_plate2.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_0hrs_plate3.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_2hrs_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_2hrs_plate4.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_2hrs_plate1.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_2hrs_plate4.output_pin('measurements'))



#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=absorbance_plate1.output_pin('measurements'))
#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=fluorescence_plate1.output_pin('measurements'))
#
#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=endpoint_absorbance_plate1.output_pin('measurements'))
#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=endpoint_fluorescence_plate1.output_pin('measurements'))
#
#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=endpoint_absorbance_plate2.output_pin('measurements'))
#protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=endpoint_fluorescence_plate2.output_pin('measurements'))
#

agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=[])
print(ee.specializations[0].markdown)
ee.specializations[0].markdown = ee.specializations[0].markdown.replace('`_E. coli_', '_`E. coli`_ `')
with open('example.md', 'w', encoding='utf-8') as f:
    f.write(ee.specializations[0].markdown)
