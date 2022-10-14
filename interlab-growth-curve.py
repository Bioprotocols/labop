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
protocol.name = 'Cell measurement protocol'
protocol.description = '''Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.'''

doc.add(protocol)
plasmids = [neg_control_plasmid, pos_control_plasmid, test_device1, test_device2, test_device3, test_device4, test_device5, test_device6]

# Day 1: Transformation
transformation = protocol.primitive_step(f'Transform',
                                          host=dh5alpha,
                                          dna=plasmids,
                                          selection_medium=lb_cam)

# Day 2: Pick colonies and culture overnight
culture_container_day1 = protocol.primitive_step('ContainerSet',
                                                 quantity=uml.LiteralInteger(value=len(plasmids)),
                                                 specification=labop.ContainerSpec(name=f'culture (day 1)',
                                                                                  queryString='cont:CultureTube',
                                                                                  prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

overnight_culture = protocol.primitive_step('Culture',
                                            inoculum=transformation.output_pin('transformants'),
                                            growth_medium=lb_cam,
                                            volume=sbol3.Measure(5, OM.millilitre),  # Actually 5-10 ml in the written protocol
                                            duration=sbol3.Measure(16, OM.hour), # Actually 16-18 hours
                                            orbital_shake_speed=sbol3.Measure(220, None),  # No unit for RPM or inverse minutes
                                            temperature=sbol3.Measure(37, OM.degree_Celsius),
                                            container=culture_container_day1.output_pin('samples'))

# Day 3 culture
culture_container_day2 = protocol.primitive_step('ContainerSet',
                                                  quantity=uml.LiteralInteger(value=len(plasmids)),
                                                  specification=labop.ContainerSpec(name=f'culture (day 2)',
                                                                                   queryString='cont:CultureTube',
                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))



back_dilution = protocol.primitive_step('Dilute',
                                        source=culture_container_day1.output_pin('samples'),
                                        destination=culture_container_day2.output_pin('samples'),
                                        diluent=lb_cam,
                                        amount=sbol3.Measure(5.0, OM.millilitre),
                                        dilution_factor=uml.LiteralInteger(value=10))

baseline_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                             samples=culture_container_day2.output_pin('samples'),
                                             wavelength=sbol3.Measure(600, OM.nanometer))

conical_tube = protocol.primitive_step('ContainerSet',
                                       quantity=uml.LiteralInteger(value=len(plasmids)),
                                       specification=labop.ContainerSpec(name=f'culture (day 2), backdiluted',
                                       queryString='cont:ConicalTube',
                                       prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))  # Should be opaque

dilution = protocol.primitive_step('DiluteToTargetOD',
                                   source=culture_container_day2.output_pin('samples'),
                                   destination=conical_tube.output_pin('samples'),
                                   diluent=lb_cam,
                                   amount=sbol3.Measure(12, OM.millilitre),
                                   target_od=sbol3.Measure(0.2, None))  # Dilute to a target OD of 0.2, opaque container

microfuge_tube_0hrs = protocol.primitive_step('ContainerSet',
                                              quantity=uml.LiteralInteger(value=len(plasmids)),
                                              specification=labop.ContainerSpec(name='absorbance timepoint (0 hrs)',
                                              queryString='cont:MicrofugeTube',
                                              prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

transfer = protocol.primitive_step('Transfer',
                                   source=conical_tube.output_pin('samples'),
                                   destination=microfuge_tube_0hrs.output_pin('samples'),
                                   amount=sbol3.Measure(0.5, OM.milliliter))

hold = protocol.primitive_step('Hold',
                               location=microfuge_tube_0hrs.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))

incubate = protocol.primitive_step('Incubate',
                                   location=conical_tube.output_pin('samples'),
                                   duration=sbol3.Measure(6, OM.hour),
                                   temperature=sbol3.Measure(37, OM.degree_Celsius),
                                   shakingFrequency=sbol3.Measure(220, None))

microfuge_tube_6hrs = protocol.primitive_step('ContainerSet',
                                              quantity=uml.LiteralInteger(value=len(plasmids)),
                                              specification=labop.ContainerSpec(name=f'absorbance timepoint (6 hrs)',
                                              queryString='cont:MicrofugeTube',
                                              prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))


transfer = protocol.primitive_step('Transfer',
                                   source=conical_tube.output_pin('samples'),
                                   destination=microfuge_tube_6hrs.output_pin('samples'),
                                   amount=sbol3.Measure(0.5, OM.milliliter))

hold = protocol.primitive_step('Hold',
                               location=microfuge_tube_6hrs.output_pin('samples'),
                               temperature=sbol3.Measure(4, OM.degree_Celsius))

# Transfer to Plate
plate = protocol.primitive_step('EmptyContainer',
                                specification=labop.ContainerSpec(name=f'measurement plate',
                                                                 queryString='cont:Plate96Well',
                                                                 prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

plan = labop.SampleData(values=quote(json.dumps({1: 'A1:D1',
                                                2: 'A2:D2',
                                                3: 'A3:D3',
                                                4: 'A4:D4',
                                                5: 'A5:D5',
                                                6: 'A6:D6',
                                                7: 'A7:D7',
                                                8: 'A8:D8',})))
transfer = protocol.primitive_step('TransferByMap',
                                    source=microfuge_tube_0hrs.output_pin('samples'),
                                    destination=plate.output_pin('samples'),
                                    amount=sbol3.Measure(100, OM.microliter),
                                    plan=plan)

plate_blanks = protocol.primitive_step('Transfer',
                                       source=[lb_cam],
                                       destination=plate.output_pin('samples'),
                                       coordinates='A9:D9',
                                       amount=sbol3.Measure(100, OM.microliter))

measure_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                             samples=plate.output_pin('samples'),
                                             wavelength=sbol3.Measure(600, OM.nanometer))
measure_fluorescence = protocol.primitive_step('MeasureFluorescence',
                                               samples=plate.output_pin('samples'),
                                               excitationWavelength=sbol3.Measure(485, OM.nanometer),
                                               emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                               emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))

protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=baseline_absorbance.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=measure_absorbance.output_pin('measurements'))
protocol.designate_output('measurements', 'http://bioprotocols.org/labop#SampleData', source=measure_fluorescence.output_pin('measurements'))


agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=[])
print(ee.specializations[0].markdown)
with open('example.md', 'w', encoding='utf-8') as f:
    f.write(ee.specializations[0].markdown)
