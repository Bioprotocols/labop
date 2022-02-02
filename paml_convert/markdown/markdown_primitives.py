# TODO: allow optionals to actually be optional

# Pre-declare the MarkdownConverter class to avoid circularity with markdown.protocol_to_markdown
class MarkdownConverter:
    pass

primitive_to_markdown_functions = {}  # dictionary of identity : function for primitives markdown conversion

#############################################
# Liquid handling primitives

LIQUID_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/liquid_handling/'


def liquid_handling_provision_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    resource = executable.input_pin('resource').to_markdown(mdc)
    destination = executable.input_pin('destination').to_markdown(mdc)
    return 'Pipette '+volume+' of '+resource+' into '+destination+'\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'Provision'] = liquid_handling_provision_to_markdown


def liquid_handling_dispense_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    source = mdc.protocol_typing.flow_values[executable.input_pin('source').input_flows().pop()]
    resource = mdc.document.find(source.specification).to_markdown(mdc) # Kludge due to document addition failures
    source_location = mdc.document.find(source.in_location[0]).to_markdown(mdc) # TODO: generalize to support multi-locations
    destination = executable.input_pin('destination').to_markdown(mdc)
    return 'Pipette '+volume+' of '+resource+' from '+source_location+' into '+destination+'\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'Dispense'] = liquid_handling_dispense_to_markdown


def liquid_handling_transfer_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    source = executable.input_pin('source').to_markdown(mdc)
    destination = executable.input_pin('destination').to_markdown(mdc)
    return 'Pipette '+volume+' from '+source+' to '+destination+'\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX + 'Transfer'] = liquid_handling_transfer_to_markdown


def liquid_handling_transferinto_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    source = executable.input_pin('source').to_markdown(mdc)
    destination = executable.input_pin('destination').to_markdown(mdc)
    mix_cycles = executable.input_pin('mixCycles').to_markdown(mdc) # TODO: this should be optional, not required
    return 'Pipette '+volume+' from '+source+' into '+destination+', mixing by pipetting up and down '+mix_cycles+' times at destination\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX + 'TransferInto'] = liquid_handling_transferinto_to_markdown


def liquid_handling_pipettemix_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    samples = executable.input_pin('samples').to_markdown(mdc)
    mix_cycles = executable.input_pin('mixCycles').to_markdown(mdc) # TODO: this should be optional, not required
    return 'Mix '+samples+' by pipetting '+volume+' up and down '+mix_cycles+' times\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'PipetteMix'] = liquid_handling_pipettemix_to_markdown


#############################################
# Plate handling primitives

PLATE_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/plate_handling/'

def plate_handling_cover_to_markdown(executable, mdc: MarkdownConverter):
    location = executable.input_pin('location').to_markdown(mdc)
    #type_uri = executable.input_pin('type').to_markdown(mdc)
    #type = type_uri.split('/')[-1] # TODO: fix kludge: need a real ontology
    #return 'Cover '+location+' with '+type+' cover\n'
    return 'Cover '+location+'\n'
primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Cover'] = plate_handling_cover_to_markdown


def plate_handling_seal_to_markdown(executable, mdc: MarkdownConverter):
    location = executable.input_pin('location').to_markdown(mdc)
    type_uri = executable.input_pin('type').to_markdown(mdc)
    type = type_uri.split('/')[-1] # TODO: fix kludge: need a real ontology
    return 'Seal '+location+' with '+type+' seal\n'
primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Seal'] = plate_handling_seal_to_markdown

# TODO: add the sealing sub-types
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'AdhesiveSeal'] = plate_handling_adhesive_seal_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'ThermalSeal'] = plate_handling_thermal_seal_to_markdown

def plate_handling_uncover_to_markdown(executable, mdc: MarkdownConverter):
    location = executable.input_pin('location').to_markdown(mdc)
    return 'Remove cover from '+location+'\n'
primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Uncover'] = plate_handling_uncover_to_markdown


def plate_handling_unseal_to_markdown(executable, mdc: MarkdownConverter):
    location = executable.input_pin('location').to_markdown(mdc)
    return 'Remove seal from '+location+'\n'
primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Unseal'] = plate_handling_unseal_to_markdown


def plate_handling_incubate_to_markdown(executable, mdc: MarkdownConverter):
    location = executable.input_pin('location').to_markdown(mdc)
    duration = executable.input_pin('duration').to_markdown(mdc)
    temperature = executable.input_pin('temperature').to_markdown(mdc)
    shakingFrequency = executable.input_pin('shakingFrequency').to_markdown(mdc) # TODO: this should be optional
    return 'Incubate '+location+' for '+duration+' at temperature '+temperature+', shaking at '+shakingFrequency+'\n'
primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Incubate'] = plate_handling_incubate_to_markdown


#############################################
# Spectrophotometry primitives

SPECTROPHOTOMETRY = 'https://bioprotocols.org/paml/primitives/spectrophotometry/'


def spectrophotometry_absorbance_to_markdown(executable, mdc: MarkdownConverter):
    samples = executable.input_pin('samples').to_markdown(mdc)
    wavelength = executable.input_pin('wavelength').to_markdown(mdc)
    return 'Measure absorbance of '+samples+' at '+wavelength+'\n'
primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureAbsorbance'] = spectrophotometry_absorbance_to_markdown


def spectrophotometry_fluorescence_to_markdown(executable, mdc: MarkdownConverter):
    samples = executable.input_pin('samples').to_markdown(mdc)
    excitation = executable.input_pin('excitationWavelength').to_markdown(mdc)
    # TODO: fix kludge: don't assume whether optionals are present
    bp_wavelength = executable.input_pin('emissionBandpassWavelength').to_markdown(mdc)
    #bp_width = executable.input_pin('emissionBandpassWidth').to_markdown(mdc)
    emission = bp_wavelength  #+' / '+bp_width
    gain = executable.input_pin('gain').to_markdown(mdc)
    return 'Measure fluorescence of '+samples+' at excitation '+excitation+' and emission '+emission+' with gain = '+gain+'\n'
primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureFluorescence'] = spectrophotometry_fluorescence_to_markdown


# TODO: add remaining primitives
# primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureFluorescenceSpectrum'] = spectrophotometry_to_markdown
