import os
import tempfile
import sbol3
import labop
import tyto
import uml
import json
import csv
import rdflib as rdfl
from typing import Dict


from labop.execution_engine import ExecutionEngine
from labop_convert.opentrons.opentrons_specialization import OT2Specialization

# Dev Note: This is a test of the initial version of the OT2 specialization. Any specs shown here can be changed in the future. Use at your own risk. Here be dragons.


def sanitize_display_id(display_id) -> str:
    invalid_chars = {c for c in display_id if not c.isalnum() and c != '_'}
    for c in invalid_chars:
        display_id = display_id.replace(c, '_')
    return display_id


def load_primer_layout(fname: str):
    '''Load layout of primer plate'''
    with open(fname, 'r') as f:
        reader = csv.DictReader(f)
        layout = {}
        for row in reader:
            primer = row['Primer']
            coordinate = row['Coordinates']
            layout[primer] = coordinate
    return layout


def load_pcr_layout(fname: str):
    '''Load layout of primer plate'''
    with open(fname, 'r') as f:
        reader = csv.DictReader(f)
        layout = {}
        for row in reader:
            f_primer = row['Forward']
            r_primer = row['Reverse']
            template = row['Template']
            coordinate = row['Coordinates']
            layout[coordinate] = dict(row)
    return layout


primer_layout = load_primer_layout('primer_layout.csv')
pcr_layout = load_pcr_layout('pcr_layout.csv')



#############################################
# set up the document
print('Setting up document')
doc = sbol3.Document()
sbol3.set_namespace('https://bbn.com/scratch/')

#############################################
# Import the primitive libraries
print('Importing libraries')
labop.import_library('liquid_handling')
print('... Imported liquid handling')
labop.import_library('plate_handling')
print('... Imported plate handling')
labop.import_library('spectrophotometry')
print('... Imported spectrophotometry')
labop.import_library('sample_arrays')
print('... Imported sample arrays')
labop.import_library('pcr')
print('... Imported pcr')


protocol = labop.Protocol('pcr_example')
protocol.name = "Opentrons PCR Demo"
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

# Configure OT2 and load it with labware
load = protocol.primitive_step('ConfigureRobot', instrument=OT2Specialization.EQUIPMENT['p300_single'], mount='left')
load = protocol.primitive_step('ConfigureRobot', instrument=OT2Specialization.EQUIPMENT['thermocycler'], mount='7')
#load = protocol.primitive_step('ConfigureRobot', instrument=OT2Specialization.EQUIPMENT['thermocycler'], mount='10')
spec_tiprack = labop.ContainerSpec('tiprack', queryString='cont:Opentrons96TipRack300uL', prefixMap=PREFIX_MAP)
load = protocol.primitive_step('LoadRackOnInstrument', rack=spec_tiprack, coordinates='1')



# Set up rack for reagents
reagent_rack = labop.ContainerSpec('reagent_rack', name='Tube rack for reagents', queryString='cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap', prefixMap=PREFIX_MAP)
rack = protocol.primitive_step('EmptyRack', specification=reagent_rack)
load_rack = protocol.primitive_step('LoadRackOnInstrument', rack=reagent_rack, coordinates='2')

# Set up primers plate
primer_plate = labop.ContainerSpec('primer_plate', name='primers in 96-well plate', queryString='cont:Corning96WellPlate360uLFlat', prefixMap=PREFIX_MAP)
load = protocol.primitive_step('LoadRackOnInstrument', rack=primer_plate, coordinates='3')
primer_plate = protocol.primitive_step('EmptyContainer', specification=primer_plate)

# Set up DNA polymerase
polymerase = labop.ContainerSpec('polymerase', name='DNA Polymerase', queryString='cont:StockReagent', prefixMap=PREFIX_MAP)
load_reagents = protocol.primitive_step('LoadContainerInRack', slots=rack.output_pin('slots'), container=polymerase, coordinates='A1')

# Set up water
load_water = protocol.primitive_step('LoadContainerInRack', slots=rack.output_pin('slots'), container=labop.ContainerSpec('water', name='tube for water', queryString='cont:MicrofugeTube', prefixMap=PREFIX_MAP) , coordinates='B1')
provision_water = protocol.primitive_step('Provision', resource=ddh2o, destination=load_water.output_pin('samples'), amount=sbol3.Measure(500, tyto.OM.microliter))


# Set up template
templates = list({reaction['Template'] for reaction in pcr_layout.values()})
templates.sort()
rack_coordinates = [f'C{i}' for i in range(1, len(templates) + 1)]
if len(templates) > 8:
    raise Exception('Too many templates')

# Automatically assign a layout for the template samples in the reagent rack
template_layout = {}
for template, coordinate in zip(templates, rack_coordinates):
    c_template = sbol3.Component('Component/' + sanitize_display_id(template), name=template, types=sbol3.SBO_DNA)
    doc.add(c_template)
    template_container = labop.ContainerSpec(sanitize_display_id(template), name='container of ' + template, queryString='cont:MicrofugeTube', prefixMap=PREFIX_MAP)
    load_template = protocol.primitive_step('LoadContainerInRack', slots=rack.output_pin('slots'), container=template_container, coordinates=coordinate)
    template_layout[template] = load_template.output_pin('samples')

# Set up PCR machine
pcr_plate = labop.ContainerSpec('pcr_plate', name='PCR plate', queryString='cont:Biorad96WellPCRPlate', prefixMap=PREFIX_MAP)
load_pcr_plate_on_thermocycler = protocol.primitive_step('LoadContainerOnInstrument', specification=pcr_plate, instrument=OT2Specialization.EQUIPMENT['thermocycler'], slots='A1:H12')

# Pipette PCR reactions
for target_well, reaction in pcr_layout.items():
    f_primer = reaction['Forward']
    f_primer_coordinates = primer_layout[f_primer]
    r_primer = reaction['Reverse']
    r_primer_coordinates = primer_layout[r_primer]
    template = template_layout[reaction['Template']]

    target_sample = protocol.primitive_step('PlateCoordinates', source=load_pcr_plate_on_thermocycler.output_pin('samples'), coordinates=target_well)

    # Transfer water
    transfer = protocol.primitive_step('Transfer', source=load_water.output_pin('samples'), destination=target_sample.output_pin('samples'), amount=sbol3.Measure(6, tyto.OM.microliter))
    transfer.name = 'Add water'

    # Transfer forward primer
    f_primer_sample = protocol.primitive_step('PlateCoordinates', source=primer_plate.output_pin('samples'), coordinates=f_primer_coordinates)
    transfer = protocol.primitive_step('Transfer', source=f_primer_sample.output_pin('samples'), destination=target_sample.output_pin('samples'), amount=sbol3.Measure(1, tyto.OM.microliter))
    transfer.name = 'Add F primer'

    # Transfer reverse primer
    r_primer_sample = protocol.primitive_step('PlateCoordinates', source=primer_plate.output_pin('samples'), coordinates=r_primer_coordinates)
    transfer = protocol.primitive_step('Transfer', source=r_primer_sample.output_pin('samples'), destination=target_sample.output_pin('samples'), amount=sbol3.Measure(1, tyto.OM.microliter))
    transfer.name = 'Add R primer'

    # Transfer template
    transfer = protocol.primitive_step('Transfer', source=template, destination=target_sample.output_pin('samples'), amount=sbol3.Measure(1, tyto.OM.microliter))
    transfer.name = 'Add template'

    # Transfer polymerase
    transfer = protocol.primitive_step('Transfer', source=load_reagents.output_pin('samples'), destination=target_sample.output_pin('samples'), amount=sbol3.Measure(1, tyto.OM.microliter))
    transfer.name = 'Add polymerase'

pcr = protocol.primitive_step('PCR',
                              denaturation_temp=sbol3.Measure(98.0, tyto.OM.degree_Celsius),
                              denaturation_time=sbol3.Measure(10, tyto.OM.second),
                              annealing_temp=sbol3.Measure(45.0, tyto.OM.degree_Celsius),
                              annealing_time=sbol3.Measure(5, tyto.OM.second),
                              extension_temp=sbol3.Measure(65.0, tyto.OM.degree_Celsius),
                              extension_time=sbol3.Measure(60, tyto.OM.second),
                              cycles=30)

filename="ot2_pcr_labop"
agent = sbol3.Agent("ot2_machine", name='OT2 machine')
ee = ExecutionEngine(specializations=[OT2Specialization(filename)], failsafe=False)
parameter_values = []
execution = ee.execute(protocol, agent, id="test_execution")

#v = doc.validate()
#assert len(v) == 0, "".join(f'\n {e}' for e in v)

doc.write('foo.ttl', file_format='ttl')

 #render and view the dot
#dot = protocol.to_dot()
#dot.render(f'{protocol.name}.gv')
#dot.view()