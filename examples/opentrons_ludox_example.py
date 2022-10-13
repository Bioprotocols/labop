import os
import tempfile
import sbol3
import paml
import tyto
import uml
import json
import rdflib as rdfl
from typing import Dict


from paml.execution_engine import ExecutionEngine
from paml_convert.opentrons.opentrons_specialization import OT2Specialization

# Dev Note: This is a test of the initial version of the OT2 specialization. Any specs shown here can be changed in the future. Use at your own risk. Here be dragons.


#############################################
# set up the document
print('Setting up document')
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


# Example of how to generate a template for a new protocol step

#print(primitives["https://bioprotocols.org/paml/primitives/liquid_handling/Dispense"].template())

protocol = paml.Protocol('iGEM_LUDOX_OD_calibration_2018')
protocol.name = "iGEM 2018 LUDOX OD calibration protocol for OT2"
protocol.description = '''
Test Execution
'''
doc.add(protocol)

# create the materials to be provisioned
CONT_NS = rdfl.Namespace('https://sift.net/container-ontology/container-ontology#')
OM_NS = rdfl.Namespace('http://www.ontology-of-units-of-measure.org/resource/om-2/')

PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'
doc.add(ddh2o)

ludox = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
ludox.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
doc.add(ludox)

p300 = sbol3.Agent('p300_single', name='P300 Single')
doc.add(p300)
load = protocol.primitive_step('ConfigureInstrument', instrument=p300, mount='left')

# Define labware
spec_rack = paml.ContainerSpec('working_reagents_rack', name='rack for reagent aliquots', queryString="cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap", prefixMap=PREFIX_MAP)
spec_ludox_container = paml.ContainerSpec('ludox_working_solution', name='tube for ludox working solution', queryString='cont:MicrofugeTube', prefixMap=PREFIX_MAP)
spec_water_container = paml.ContainerSpec('water_stock', name='tube for water aliquot', queryString='cont:MicrofugeTube', prefixMap=PREFIX_MAP)
spec_plate = paml.ContainerSpec('calibration_plate', name='calibration plate', queryString='cont:Corning96WellPlate360uLFlat', prefixMap=PREFIX_MAP)
spec_tiprack = paml.ContainerSpec('tiprack', queryString='cont:Opentrons96TipRack300uL', prefixMap=PREFIX_MAP)
doc.add(spec_rack)
doc.add(spec_ludox_container)
doc.add(spec_water_container)
doc.add(spec_plate)
doc.add(spec_tiprack)

# Load OT2 instrument with labware
load = protocol.primitive_step('LoadRackOnInstrument', rack=spec_rack, coordinates='1')
load = protocol.primitive_step('LoadRackOnInstrument', rack=spec_tiprack, coordinates='2')
load = protocol.primitive_step('LoadRackOnInstrument', rack=spec_plate, coordinates='3')


# Set up reagents
rack = protocol.primitive_step('EmptyRack', specification=spec_rack)
load_rack1 = protocol.primitive_step('LoadContainerInRack', slots=rack.output_pin('slots'), container=spec_ludox_container, coordinates='A1')
load_rack2 = protocol.primitive_step('LoadContainerInRack', slots=rack.output_pin('slots'), container=spec_water_container, coordinates='A2')
provision = protocol.primitive_step('Provision', resource=ludox, destination=load_rack1.output_pin('samples'), amount=sbol3.Measure(500, tyto.OM.microliter))
provision = protocol.primitive_step('Provision', resource=ddh2o, destination=load_rack2.output_pin('samples'), amount=sbol3.Measure(500, tyto.OM.microliter))


# Set up target samples
plate = protocol.primitive_step('EmptyContainer', specification=spec_plate)
water_samples = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates="A1:D1")
ludox_samples = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates="A2:D2")




transfer = protocol.primitive_step('Transfer', source=load_rack1.output_pin('samples'), destination=water_samples.output_pin('samples'),amount=sbol3.Measure(100, tyto.OM.microliter))
transfer = protocol.primitive_step('Transfer', source=load_rack1.output_pin('samples'), destination=ludox_samples.output_pin('samples'),amount=sbol3.Measure(100, tyto.OM.microliter))


filename="ot2_ludox_paml"
agent = sbol3.Agent("ot2_machine", name='OT2 machine')
ee = ExecutionEngine(specializations=[OT2Specialization(filename)])
parameter_values = []
execution = ee.execute(protocol, agent, id="test_execution")

#v = doc.validate()
#assert len(v) == 0, "".join(f'\n {e}' for e in v)

doc.write('foo.ttl', file_format='ttl')

 #render and view the dot
#dot = protocol.to_dot()
#dot.render(f'{protocol.name}.gv')
#dot.view()
