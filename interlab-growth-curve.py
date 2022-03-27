'''
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
'''
import paml
import sbol3
from tyto import OM
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

# vortex = protocol.primitive_step(
# 	'Vortex',
# 	amount='',
# 	destination='',
# 	source='',
# 	dispenseVelocity=''
# 	)


# create the materials to be provisioned
dh5alpha = sbol3.Component('dh5alpha', 'https://identifiers.org/pubchem.substance:24901740')
dh5alpha.name = 'E. coli DH5 alpha'  
doc.add(dh5alpha)

lb_cam = sbol3.Component('lb_cam', 'https://identifiers.org/pubchem.substance:24901740')
lb_cam.name = 'LB Broth + chloramphenicol'  
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
protocol.description = '''Prior to performing the cell measurements you should perform all three of
the calibration measurements. Please do not proceed unless you have
completed the three calibration protocols.
Completion of the calibrations will ensure that you understand the measurement process and that
you can take the cell measurements under the same conditions. For the sake of consistency and
reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to
this strain, you can request streaks of the transformed devices from another team near you, and this
can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you
are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study
by contacting the Measurement Committee (measurement at igem dot org) to discuss your
situation.
For all of these cell measurements, you must use the same plates and volumes that you used in your
calibration protocol. You must also use the same settings (e.g., filters or excitation and emission
wavelengths) that you used in your calibration measurements. If you do not use the same plates,
volumes, and settings, the measurements will not be valid.'''
doc.add(protocol)



'''
Prepare the stock solution
'''


plasmids = [neg_control_plasmid, pos_control_plasmid, test_device1, test_device2, test_device3, test_device4, test_device5, test_device6]
transformant_colonies = []
i_transformant_clone = 0
for plasmid in plasmids[:1]:
    # Day 1: Transformation
    transformation = protocol.primitive_step(f'Transform',
                                             host=dh5alpha,
                                             dna=plasmid,
                                             selection_medium=lb_cam)
    # Day 2: Pick colonies and culture overnight
    for i_replicates in range(0, 2):

        i_transformant_clone += 1
        culture_container = protocol.primitive_step('EmptyContainer', 
                                                     specification=paml.ContainerSpec(name=f'{plasmid.name} culture',
                                                                                      queryString='cont:Container', 
                                                                                      prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
            
        overnight_culture = protocol.primitive_step(f'Culture',
                                               inoculum=transformation.output_pin('transformants'),
                                               growth_medium=lb_cam,  # Actually LB+chloramphenicol
                                               volume=sbol3.Measure(5, OM.millilitre),  # Actually 5-10 ml in the written protocol
                                               duration=sbol3.Measure(16, OM.hour), # Actually 16-18 hours
                                               orbital_shake_speed=sbol3.Measure(220, None),  # No unit for RPM or inverse minutes
                                               temperature=sbol3.Measure(37, OM.degree_Celsius),
                                               container=culture_container.output_pin('samples'))

        # Day 3 culture
        culture_container = protocol.primitive_step('EmptyContainer', 
                                                     specification=paml.ContainerSpec(name=f'{plasmid.name} culture',
                                                                                      queryString='cont:Container', 
                                                                                      prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
        
        back_dilution = protocol.primitive_step('Transfer',
                                                source=lb_cam,
                                                destination=culture_container.output_pin('samples'),
                                                amount=sbol3.Measure(4.5, OM.millilitre))
        back_dilution = protocol.primitive_step('Transfer',
                                                source=overnight_culture.output_pin('culture'),
                                                destination=culture_container.output_pin('samples'),
                                                amount=sbol3.Measure(0.5, OM.millilitre))

        absorbance = protocol.primitive_step('MeasureAbsorbance',
                                             samples=culture_container.output_pin('samples'),
                                             wavelength=sbol3.Measure(600, OM.nanometer))

        conical_tube = protocol.primitive_step('EmptyContainer', 
                                              specification=paml.ContainerSpec(name=f'Conical tube {i_transformant_clone}: {plasmid.name}',
                                                                               queryString='cont:ConicalTube', 
                                                                               prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

        dilution = protocol.primitive_step('DiluteToTargetOD',
                                           source=culture_container.output_pin('samples'),
                                           destination=conical_tube.output_pin('samples'),
                                           diluent=lb_cam,
                                           amount=sbol3.Measure(12, OM.millilitre),
                                           target_od=sbol3.Measure(0.2, None))  # Dilute to a target OD of 0.2, opaque container
        
        incubate = protocol.primitive_step('Incubate',
                                           location=conical_tube.output_pin('samples'),
                                           duration=sbol3.Measure(6, OM.hour),
                                           temperature=sbol3.Measure(37, OM.degree_Celsius),
                                           shakingFrequency=sbol3.Measure(220, None))
        
        
        
        microfuge_tube = protocol.primitive_step('EmptyContainer', 
                                                specification=paml.ContainerSpec(name=f'Microfuge tube {i_transformant_clone}: {plasmid.name}',
                                                                               queryString='cont:MicrofugeTube', 
                                                                               prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))
        
agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
parameter_values = [
]
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)        
