import sbol3
import paml
import paml_md


# Pre-declare the MarkdownConverter class to avoid circularity with paml_md.protocol_to_markdown
class MarkdownConverter:
    pass

primitive_to_markdown_functions = {}  # dictionary of identity : function for primitives markdown conversion

#############################################
# Liquid handling primitives

LIQUID_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/liquid_handling/'

# TODO: add amount information into sample records


def liquid_handling_provision_to_markdown(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    resource = executable.input_pin('resource').to_markdown(mdc)
    location = executable.input_pin('destination').to_markdown(mdc)
    return 'Pipette '+volume+' of '+resource+' into '+location+'\n'
primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'Provision'] = liquid_handling_provision_to_markdown


# TODO: implement rest
# primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'Dispense'] = liquid_handling_dispense_to_markdown
# primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX + 'Transfer'] = liquid_handling_transfer_to_markdown
# primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX + 'TransferInto'] = liquid_handling_transferinto_to_markdown
# primitive_to_markdown_functions[LIQUID_HANDLING_PREFIX+'PipetteMix'] = no_output_primitive_to_markdown

#############################################
# Plate handling primitives

PLATE_HANDLING_PREFIX = 'https://bioprotocols.org/paml/primitives/liquid_handling/'

# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Cover'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Seal'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'AdhesiveSeal'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'ThermalSeal'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Uncover'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Unseal'] = no_output_primitive_to_markdown
# primitive_to_markdown_functions[PLATE_HANDLING_PREFIX+'Incubate'] = no_output_primitive_to_markdown


#############################################
# Spectrophotometry primitives

SPECTROPHOTOMETRY = 'https://bioprotocols.org/paml/primitives/spectrophotometry/'


def spectrophotometry_absorbance_to_markdown(executable, mdc: MarkdownConverter):
    samples = executable.input_pin('samples').to_markdown(mdc)
    wavelength = executable.input_pin('wavelength').to_markdown(mdc)
    return 'Measure absorbance of '+samples+' at '+wavelength+'\n'
primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureAbsorbance'] = spectrophotometry_absorbance_to_markdown

# primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureFluorescence'] = spectrophotometry_to_markdown
# primitive_to_markdown_functions[SPECTROPHOTOMETRY+'MeasureFluorescenceSpectrum'] = spectrophotometry_to_markdown
