import sbol3
import paml
import paml.type_inference

class ProtocolTyping:pass

primitive_type_inference_functions = {}  # dictionary of identity : function for typing primitives

# When there is no output, we don't need to do any inference
def no_output_primitive_infer_typing(executable, typing: ProtocolTyping):
    pass

#############################################
# Liquid handling primitives

LIQUID_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/liquid_handling/'

# TODO: add amount information into sample records

def liquid_handling_provision_infer_typing(executable, typing: ProtocolTyping):
    resource = executable.input_pin('resource').input_type(typing)
    location = executable.input_pin('destination').input_type(typing)
    samples = paml.ReplicateSamples(specification = resource)
    samples.in_location.append(location)
    executable.output_pin('samples').assert_output_type(typing, samples)
primitive_type_inference_functions[LIQUID_HANDLING_PREFIX+'Provision'] = liquid_handling_provision_infer_typing

def liquid_handling_dispense_infer_typing(executable, typing: ProtocolTyping):
    source = executable.input_pin('source').input_type(typing)  # Assumed singular replicate
    location = executable.input_pin('destination').input_type(typing)
    samples = paml.ReplicateSamples(specification = resource)
    samples.in_location.append(location)
    executable.output_pin('samples').assert_output_type(typing, samples)
primitive_type_inference_functions[LIQUID_HANDLING_PREFIX+'Dispense'] = liquid_handling_dispense_infer_typing

###############
# TODO: create logic to merge sample specifications as they get transferred and mixed

# TODO: generalize to allow multiple containers, non-identical locations
# TODO: track amounts as well

# TODO: this is a kludge that needs to be generalized to handle transfers between non-identical locations
def translate_sublocation(source: paml.ContainerCoordinates, destination: paml.Container):
    return paml.ContainerCoordinates(in_location = destination, coordinates = source.coordinates)

def heterogeneous_relocated_samples(self, destination: paml.Location):
    assert (len(self.containers == 1))
    relocated = paml.HeterogeneousSamples()
    relocated.replicate_samples = {r.relocated_samples(translate_sublocation(r.in_location,destination)) for r in self.replicate_samples}
paml.HeterogeneousSamples.relocated_samples = heterogeneous_relocated_samples

def replicate_relocated_samples(self, destination: paml.Location):
    assert(len(self.containers==1))
    relocated = paml.ReplicateSamples(specification=self.specification)
    relocated.in_location.append(destination)
    return relocated
paml.ReplicateSamples.relocated_samples = replicate_relocated_samples

def liquid_handling_transfer_infer_typing(executable, typing: ProtocolTyping):
    source = executable.input_pin('source').input_type(typing)
    destination = executable.input_pin('destination').input_type(typing)
    amount = executable.input_pin('amount').input_type(typing)
    samples = source.relocated_samples(destination)
    executable.output_pin('samples').assert_output_type(typing, samples)
primitive_type_inference_functions[LIQUID_HANDLING_PREFIX + 'Transfer'] = liquid_handling_transfer_infer_typing


# def liquid_handling_transferinto_infer_typing(executable, typing: ProtocolTyping):
#     source = executable.input_pin('source').input_type(typing)
#     destination = executable.input_pin('destination').input_type(typing)
#     # The samples will now consist of a combination of the original and the added material
#
#     joint_contents = sbol3.Component(executable.display_id+'_contents', sbol3.SBO_FUNCTIONAL_ENTITY) # TODO: generalize for SubProtocol inference
#     joint_contents.features.append(sbol3.SubComponent(source.specification))
#     joint_contents.features.append(sbol3.SubComponent(destination.specification))
#     samples = paml.ReplicateSamples(specification = joint_contents)
#     samples.in_location.append(location)
#     executable.output_pin('samples').assert_output_type(typing, samples)
# primitive_type_inference_functions[LIQUID_HANDLING_PREFIX+'TransferInto'] = liquid_handling_transferinto_infer_typing
#
#
# p = paml.Primitive('TransferInto')
# p.description = 'Mix a measured volume taken from an array of source samples intto an identically shaped array of destination samples'
# p.add_input('source', 'http://bioprotocols.org/paml#LocatedSamples')
# p.add_input('destination', 'http://bioprotocols.org/paml#LocatedSamples')
# p.add_input('amount', sbol3.OM_MEASURE) # Must be volume
# p.add_input('mixCycles', sbol3.OM_MEASURE, True)
# p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
# p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
# doc.add(p)


primitive_type_inference_functions[LIQUID_HANDLING_PREFIX+'PipetteMix'] = no_output_primitive_infer_typing

#############################################
# Plate handling primitives

PLATE_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/liquid_handling/'

primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'Cover'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'Seal'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'AdhesiveSeal'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'ThermalSeal'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'Uncover'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'Unseal'] = no_output_primitive_infer_typing
primitive_type_inference_functions[PLATE_HANDLING_PREFIX+'Incubate'] = no_output_primitive_infer_typing


#############################################
# Spectrophotometry primitives

SPECTROPHOTOMETRY_PREFIX = 'https://bioprotocols.org/paml/primitives/spectrophotometry/'

def spectrophotometry_plate_measurement_infer_typing(executable, typing: ProtocolTyping):
    samples = executable.input_pin('samples').input_type(typing)
    # TODO: make this a LocatedData rather than just copying the samples
    # samples = paml.LocatedData()
    executable.output_pin('measurements').assert_output_type(typing, samples)
primitive_type_inference_functions[SPECTROPHOTOMETRY_PREFIX+'MeasureAbsorbance'] = spectrophotometry_plate_measurement_infer_typing
primitive_type_inference_functions[SPECTROPHOTOMETRY_PREFIX+'MeasureFluorescence'] = spectrophotometry_plate_measurement_infer_typing
primitive_type_inference_functions[SPECTROPHOTOMETRY_PREFIX+'MeasureFluorescenceSpectrum'] = spectrophotometry_plate_measurement_infer_typing

