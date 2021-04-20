import sbol3
import paml
import tyto

#############################################
# Helper functions

# set up the document
doc = sbol3.Document()
sbol3.set_namespace('https://sd2e.org/PAML/')

#############################################
# Import the primitive libraries
print('Importing libraries')
paml.import_library('liquid_handling')
paml.import_library('plate_handling')
paml.import_library('spectrophotometry')

# this should really get pulled into a common library somewhere
rpm = sbol3.UnitDivision('rpm',name='rpm', symbol='rpm',label='revolutions per minute',numerator=tyto.OM.revolution,denominator=tyto.OM.minute)
doc.add(rpm)


#############################################
# Create the protocols

print('Constructing measurement sub-protocols')
# This will be used 10 times generating "OD_Plate_1" .. "OD_Plate_9"

split_and_measure = paml.Protocol('SplitAndMeasure', name="Split samples, dilute, and measure")
split_and_measure.description = '''
Subprotocol to split a portion of each sample in a plate into another plate, diluting 
with PBS, then measure OD and fluorescence from that other plate
'''
doc.add(split_and_measure)

# plate for split-and-measure subroutine
od_plate = paml.Container(name='OD Plate', type=tyto.NCIT.Microplate, max_coordinate='H12')
split_and_measure.locations = {od_plate}

# Inputs: collection of samples, pbs_source
samples = split_and_measure.add_input(name='samples', description='Samples to measure', type='http://bioprotocols.org/paml#LocatedSamples')
pbs_source = split_and_measure.add_input(name='pbs', description='Source for PBS', type='http://bioprotocols.org/paml#LocatedSamples')

# subprotocol steps
s_p = split_and_measure.execute_primitive('Dispense', source=pbs_source, destination=od_plate,
                                          amount=sbol3.Measure(90, tyto.OM.microliter))
split_and_measure.add_flow(split_and_measure.initial(), s_p) # dispensing OD can be a first action
s_u = split_and_measure.execute_primitive('Unseal', location=samples)
split_and_measure.add_flow(split_and_measure.initial(), s_u) # unsealing the growth plate can be a first action
s_t = split_and_measure.execute_primitive('TransferInto', source=samples, destination=s_p.output_pin('samples'),
                                          amount=sbol3.Measure(10, tyto.OM.microliter),
                                          mixCycles=sbol3.Measure(10, tyto.OM.number))
split_and_measure.add_flow(s_u, s_t) # transfer can't happen until growth plate is unsealed

# add the measurements, in parallel
ready_to_measure = paml.Fork()
split_and_measure.activities.append(ready_to_measure)
split_and_measure.add_flow(s_t.output_pin('samples'), ready_to_measure)
measurement_complete = paml.Join()
split_and_measure.activities.append(measurement_complete)

s_a = split_and_measure.execute_primitive('MeasureAbsorbance', samples=ready_to_measure,
                                          wavelength=sbol3.Measure(600, tyto.OM.nanometer),
                                          numFlashes=sbol3.Measure(25, tyto.OM.number))
v_a = split_and_measure.add_output('absorbance', s_a.output_pin('measurements'))
split_and_measure.add_flow(v_a, measurement_complete)

gains = {0.1, 0.2, 0.16}
for g in gains:
    s_f = split_and_measure.execute_primitive('MeasureFluorescence', samples=ready_to_measure,
                                              excitationWavelength=sbol3.Measure(488, tyto.OM.nanometer),
                                              emissionBandpassWavelength=sbol3.Measure(530, tyto.OM.nanometer),
                                              numFlashes=sbol3.Measure(25, tyto.OM.number),
                                              gain=sbol3.Measure(g, tyto.OM.number))
    v_f = split_and_measure.add_output('fluorescence_'+str(g), s_f.output_pin('measurements'))
    split_and_measure.add_flow(v_f, measurement_complete)

s_c = split_and_measure.execute_primitive('Cover', location=od_plate)
split_and_measure.add_flow(measurement_complete, s_c)
split_and_measure.add_flow(s_c, split_and_measure.final())

s_s = split_and_measure.execute_primitive('Seal', location=samples,
                                          type='http://autoprotocol.org/lids/breathable') # need to turn this into a proper ontology
split_and_measure.add_flow(measurement_complete, s_s)
split_and_measure.add_flow(s_s, split_and_measure.final())

print('Measurement sub-protocol construction complete')



overnight_od_measure = paml.Protocol('OvernightODMeasure', name="Split samples and measure, without dilution")
overnight_od_measure.description = '''
Subprotocol to split a portion of each sample in an unsealed plate into another plate, then measure OD and fluorescence from that other plate
'''
doc.add(overnight_od_measure)

# plate for split-and-measure subroutine
od_plate = paml.Container(name='OD Plate', type=tyto.NCIT.Microplate, max_coordinate='H12')
overnight_od_measure.locations = {od_plate}

# Input: collection of samples
samples = overnight_od_measure.add_input(name='samples', description='Samples to measure', type='http://bioprotocols.org/paml#LocatedSamples')

# subprotocol steps
s_t = overnight_od_measure.execute_primitive('Transfer', source=samples, destination=od_plate,
                                          amount=sbol3.Measure(200, tyto.OM.microliter))
overnight_od_measure.add_flow(overnight_od_measure.initial(), s_t) # first action

# add the measurements, in parallel
ready_to_measure = paml.Fork()
overnight_od_measure.activities.append(ready_to_measure)
overnight_od_measure.add_flow(s_t.output_pin('samples'), ready_to_measure)
measurement_complete = paml.Join()
overnight_od_measure.activities.append(measurement_complete)

s_a = overnight_od_measure.execute_primitive('MeasureAbsorbance', samples=ready_to_measure,
                                          wavelength=sbol3.Measure(600, tyto.OM.nanometer),
                                          numFlashes=sbol3.Measure(25, tyto.OM.number))
v_a = overnight_od_measure.add_output('absorbance', s_a.output_pin('measurements'))
overnight_od_measure.add_flow(v_a, measurement_complete)

gains = {0.1, 0.2, 0.16}
for g in gains:
    s_f = overnight_od_measure.execute_primitive('MeasureFluorescence', samples=ready_to_measure,
                                              excitationWavelength=sbol3.Measure(488, tyto.OM.nanometer),
                                              emissionBandpassWavelength=sbol3.Measure(530, tyto.OM.nanometer),
                                              numFlashes=sbol3.Measure(25, tyto.OM.number),
                                              gain=sbol3.Measure(g, tyto.OM.number))
    v_f = overnight_od_measure.add_output('fluorescence_'+str(g), s_f.output_pin('measurements'))
    overnight_od_measure.add_flow(v_f, measurement_complete)

s_c = overnight_od_measure.execute_primitive('Cover', location=od_plate)
overnight_od_measure.add_flow(measurement_complete, s_c)
overnight_od_measure.add_flow(s_c, overnight_od_measure.final())

overnight_od_measure.add_flow(measurement_complete, overnight_od_measure.final())

print('Overnight measurement sub-protocol construction complete')
#############################################
# Now the full protocol

print('Making protocol')

protocol = paml.Protocol('GrowthCurve', name = "SD2 Yeast growth curve protocol")
protocol.description = '''
Protocol from SD2 Yeast States working group for studying growth curves:
Grow up cells and read with plate reader at n-hour intervals
'''
doc.add(protocol)

# Create the materials to be provisioned
PBS = sbol3.Component('PBS', 'https://identifiers.org/pubchem.substance:24978514')
PBS.name = 'Phosphate-Buffered Saline'  # I'd like to get this name from PubChem with tyto
doc.add(PBS)
# need to retrieve and convert this one
SC_media = sbol3.Component('SC_Media', 'TBD', name='Synthetic Complete Media')
doc.add(SC_media)
SC_plus_dox = sbol3.Component('SC_Media_plus_dox', 'TBD', name='Synthetic Complete Media plus 40nM Doxycycline')
doc.add(SC_plus_dox)
protocol.material += {PBS, SC_media, SC_plus_dox}

## create the containers
# provisioning sources
pbs_source = paml.Container(name='PBS Source', type=tyto.NCIT.Bottle)
sc_source = paml.Container(name='SC Media + 40nM Doxycycline Source', type=tyto.NCIT.Bottle)
om_source = paml.Container(name='Overnight SC Media Source', type=tyto.NCIT.Bottle)
# plates for the general protocol
overnight_plate = paml.Container(name='Overnight Growth Plate', type=tyto.NCIT.Microplate, max_coordinate='H12')
overnight_od_plate = paml.Container(name='Overnight Growth Plate', type=tyto.NCIT.Microplate, max_coordinate='H12')
growth_plate = paml.Container(name='Growth Curve Plate', type=tyto.NCIT.Microplate, max_coordinate='H12')
protocol.locations = {pbs_source, sc_source, om_source, overnight_plate, growth_plate}

# One input: a microplate full of strains
# TODO: change this to allow alternative places
strain_plate = protocol.add_input(name='strain_plate', description='Plate of strains to grow', type='http://bioprotocols.org/paml#LocatedSamples')
#input_plate = paml.Container(name='497943_4_UWBF_to_stratoes', type=tyto.NCIT.Microplate, max_coordinate='H12')

print('Constructing protocol steps')

# set up the sources
p_pbs = protocol.execute_primitive('Provision', resource=PBS, destination=pbs_source,
                                   amount=sbol3.Measure(117760, tyto.OM.microliter))
protocol.add_flow(protocol.initial(), p_pbs) # start with provisioning
p_om = protocol.execute_primitive('Provision', resource=SC_media, destination=om_source,
                                   amount=sbol3.Measure(98, tyto.OM.milliliter))
protocol.add_flow(protocol.initial(), p_om) # start with provisioning
p_scm = protocol.execute_primitive('Provision', resource=SC_plus_dox, destination=sc_source,
                                   amount=sbol3.Measure(117200, tyto.OM.microliter))
protocol.add_flow(protocol.initial(), p_scm) # start with provisioning

# prep the overnight culture, then seal away the source plate again
s_d = protocol.execute_primitive('Dispense', source=p_om.output_pin('samples'), destination=overnight_plate,
                                          amount=sbol3.Measure(500, tyto.OM.microliter))
s_u = protocol.execute_primitive('Unseal', location=strain_plate)
s_t = protocol.execute_primitive('TransferInto', source=strain_plate, destination=s_d.output_pin('samples'),
                                 amount=sbol3.Measure(5, tyto.OM.microliter),
                                 mixCycles = sbol3.Measure(10, tyto.OM.number))
s_s = protocol.execute_primitive('Seal', location=strain_plate,
                                 type='http://autoprotocol.org/lids/breathable') # need to turn this into a proper ontology
protocol.add_flow(s_u, s_t) # transfer can't happen until strain plate is unsealed ...
protocol.add_flow(s_t, s_s) # ... and must complete before we re-seal it

# run the overnight culture
overnight_samples = s_t.output_pin('samples')
s_s = protocol.execute_primitive('Seal', location=overnight_samples,
                                 type='http://autoprotocol.org/lids/breathable') # need to turn this into a proper ontology
s_i = protocol.execute_primitive('Incubate', location=overnight_samples,
                                 temperature=sbol3.Measure(30, tyto.OM.get_uri_by_term('degree Celsius')),
                                 duration=sbol3.Measure(16, tyto.OM.hour),
                                 shakingFrequency=sbol3.Measure(350, rpm.identity))
protocol.add_flow(s_s, s_i) # incubation after sealing

# Check the OD after running overnight; note that this is NOT the same measurement process as for the during-growth measurements
s_u = protocol.execute_primitive('Unseal', location=overnight_samples) # added because using the subprotocol leaves a sealed plate
protocol.add_flow(s_i, s_u) # growth plate after measurement
s_m = protocol.execute_subprotocol(overnight_od_measure, samples=overnight_samples)
protocol.add_flow(s_m, protocol.final()) # measurement after incubation

# Set up the growth plate
s_d = protocol.execute_primitive('Dispense', source=p_scm.output_pin('samples'), destination=growth_plate,
                                 amount=sbol3.Measure(700, tyto.OM.microliter))
s_t = protocol.execute_primitive(doc.find('TransferInto'), source=overnight_samples, destination=s_d.output_pin('samples'),
                                 amount=sbol3.Measure(2, tyto.OM.microliter),
                                 mixCycles = sbol3.Measure(10, tyto.OM.number))
s_s = protocol.execute_primitive('Seal', location=overnight_samples,
                                 type='http://autoprotocol.org/lids/breathable') # need to turn this into a proper ontology
protocol.add_flow(s_u, s_t) # transfer can't happen until strain plate is unsealed ...
protocol.add_flow(s_t, s_s) # ... and must complete before we re-seal it

# run the step-by-step culture
growth_samples = s_t.output_pin('samples')
last_round = None
# sample_hours = [1, 3, 6, 9, 12, 15, 18, 21, 24]   # Original: modified to be friendly to human execution
sample_hours = [1, 3, 6, 9, 18, 21, 24]
for i in range(0,len(sample_hours)):
    incubation_hours = sample_hours[i] - (sample_hours[i-1] if i>0 else 0)
    s_i = protocol.execute_primitive('Incubate', location=growth_samples,
                                    temperature=sbol3.Measure(30, tyto.OM.get_uri_by_term('degree Celsius')),
                                    duration=sbol3.Measure(incubation_hours, tyto.OM.hour),
                                    shakingFrequency=sbol3.Measure(350, rpm.identity))
    s_m = protocol.execute_subprotocol(split_and_measure, samples=growth_samples, pbs=p_pbs.output_pin('samples'))
    if last_round:
        protocol.add_flow(last_round, s_i) # measurement after incubation
    protocol.add_flow(s_i, s_m) # measurement after incubation
    last_round = s_m

protocol.add_flow(last_round, protocol.final())

print('Protocol construction complete')


######################
# Invocation of protocol on a plate:;

# plate for invoking the protocol
#input_plate = paml.Container(name='497943_4_UWBF_to_stratoes', type=tyto.NCIT.Microplate, max_coordinate='H12')


print('Validating document')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

print('Writing document')

doc.write('test/testfiles/growth_curve.json','json-ld')
doc.write('test/testfiles/growth_curve.ttl','turtle')

print('Complete')
