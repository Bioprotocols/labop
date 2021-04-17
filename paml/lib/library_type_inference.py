import paml
import paml.type_inference

class ProtocolTyping:pass

primitive_type_inference_functions = {}  # dictionary of identity : function for typing primitives


def liquid_handling_Provision_infer_typing(executable, typing: ProtocolTyping):
    resource = executable.input_pin('resource').input_type(typing)
    location = executable.input_pin('destination').input_type(typing)
    samples = paml.ReplicateSamples(specification = resource)
    samples.in_location.append(location)
    executable.output_pin('samples').assert_output_type(typing, samples)
primitive_type_inference_functions['https://bioprotocols.org/paml/primitives/liquid_handling/Provision'] = liquid_handling_Provision_infer_typing

def spectrophotometry_MeasureAbsorbance_infer_typing(executable, typing: ProtocolTyping):
    samples = executable.input_pin('samples').input_type(typing)
    # TODO: make this a LocatedData rather than just copying the samples
    # samples = paml.LocatedData()
    executable.output_pin('measurements').assert_output_type(typing, samples)
primitive_type_inference_functions['https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance'] = spectrophotometry_MeasureAbsorbance_infer_typing
