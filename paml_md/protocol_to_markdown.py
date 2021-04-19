import sbol3
import paml
import tyto
import openpyxl
import os
import posixpath
import paml.type_inference
from copy import copy

##############################################
# Direct conversion of individual PAML objects to markdown

# TODO: make this build PROV-O as it goes?
class MarkdownConverter():
    def __init__(self, document: sbol3.Document, protocol_typing: paml.type_inference.ProtocolTyping):
        self.protocol_typing = protocol_typing
        self.document = document

    def markdown_header(self, protocol):
        header = '# ' + (protocol.display_id if (protocol.name is None) else protocol.name) + '\n'
        header += '\n'
        header += '## Description:\n' + (
            'No description given' if protocol.description is None else protocol.description) + '\n'
        return header


##############################################
# Direct conversion of individual PAML objects to markdown


def measure_to_markdown(self: sbol3.Measure, mdc: MarkdownConverter):
    return str(self.value) + ' ' + str(tyto.OM.get_term_by_uri(self.unit))
sbol3.Measure.to_markdown = measure_to_markdown


def component_to_markdown(self: sbol3.Component, mdc: MarkdownConverter):
    return '[' + (self.display_id if (self.name is None) else self.name) + ']('+self.types[0]+')'
sbol3.Component.to_markdown = component_to_markdown


def container_to_markdown(self: paml.Container, mdc: MarkdownConverter):
    return '[' + (self.display_id if (self.name is None) else self.name) + ']('+self.type+')'
paml.Container.to_markdown = container_to_markdown


def containercoodinates_to_markdown(self: paml.ContainerCoordinates, mdc: MarkdownConverter):
    return self.in_container.lookup().to_markdown(mdc) + ' ' + self.coordinates
paml.ContainerCoordinates.to_markdown = containercoodinates_to_markdown

##############################################
# old code being reprocessed

def markdown_mergedlocations(location_list, mdc: MarkdownConverter):
    this = location_list.pop().to_markdown(mdc)
    if len(location_list) == 0:
        return this
    if len(location_list) == 1:
        return this + ' and ' + markdown_mergedlocations(location_list, mdc)
    else:
        return this + ', ' + markdown_mergedlocations(location_list, mdc)

def markdown_flow_value(value, mdc: MarkdownConverter):
    if isinstance(value, paml.LocatedData):
        value = value.from_samples  # unwrap value

    if isinstance(value, paml.ReplicateSamples):
        return markdown_mergedlocations({x.lookup() for x in value.in_location}, mdc)
    elif isinstance(value, paml.HeterogeneousSamples):
        return markdown_mergedlocations({mdc.document.find(loc) for rep in value.replicate_samples for loc in rep.in_location}, mdc)
    # if we fall through to here:
    return str(value)


def simplevaluepin_to_markdown(self: paml.SimpleValuePin, mdc: MarkdownConverter):
    return str(self.value)
paml.SimpleValuePin.to_markdown = simplevaluepin_to_markdown


def localvaluepin_to_markdown(self: paml.LocalValuePin, mdc: MarkdownConverter):
    return self.value.to_markdown(mdc)
paml.LocalValuePin.to_markdown = localvaluepin_to_markdown


def referencevaluepin_to_markdown(self: paml.ReferenceValuePin, mdc: MarkdownConverter):
    return self.value.lookup().to_markdown(mdc)
paml.ReferenceValuePin.to_markdown = referencevaluepin_to_markdown


def pin_to_markdown(self: paml.Pin, mdc: MarkdownConverter):
    protocol = self.get_toplevel()
    executable = self.get_parent()
    value = mdc.protocol_typing.flow_values[next(x for x in protocol.flows if x.sink.lookup() in executable.input)]
    return markdown_flow_value(value, mdc)
paml.Pin.to_markdown = pin_to_markdown


############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def markdown_provision(executable, mdc: MarkdownConverter):
    volume = executable.input_pin('amount').to_markdown(mdc)
    resource = executable.input_pin('resource').to_markdown(mdc)
    location = executable.input_pin('destination').to_markdown(mdc)
    instruction = 'Pipette '+volume+' of '+resource+' into '+location+'\n'
    return instruction

############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def markdown_absorbance(executable, mdc: MarkdownConverter):
    samples = executable.input_pin('samples').to_markdown(mdc)
    wavelength = executable.input_pin('wavelength').to_markdown(mdc)
    instruction = 'Measure absorbance of '+samples+' at '+wavelength+'\n'
    return instruction

#################
# All this stuff should be transformed into visitor patterns
primitive_library = {
    'https://bioprotocols.org/paml/primitives/liquid_handling/Provision' : markdown_provision,
    'https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance' : markdown_absorbance
}

def primitiveexecutable_to_markdown(self: paml.PrimitiveExecutable, mdc: MarkdownConverter):
    stepwriter = primitive_library[mdc.document.find(self.instance_of).identity]
    assert stepwriter
    return stepwriter(self, mdc)
paml.PrimitiveExecutable.to_markdown = primitiveexecutable_to_markdown


def value_to_markdown(self: paml.Value, mdc: MarkdownConverter):
    return 'Report values from '+markdown_flow_value(mdc.protocol_typing.flow_values[self.input_flows().pop()], mdc)+'\n'
paml.Value.to_markdown = value_to_markdown


#############

def markdown_material(component, mdc: MarkdownConverter):
    bullet = '* ' + component.to_markdown(mdc)
    if component.description is not None: bullet += ': ' + component.description
    bullet += '\n'
    return bullet

def markdown_container_toplevel(container, mdc: MarkdownConverter):
    bullet = '* ' + container.to_markdown(mdc)
    if container.description is not None: bullet += ': ' + container.description
    return bullet

def unpin_activity(protocol, activity):
    if isinstance(activity,paml.Pin):
        owner = next(x for x in protocol.activities if isinstance(x,paml.Executable) and
                     (activity in x.output or activity in protocol.input))
        return owner
    else:
        return activity


##############################
# For serializing activities
def direct_precedents(protocol, activity):
    assert activity in protocol.activities
    flows = (x for x in protocol.flows if (x.sink.lookup() == activity) or (isinstance(activity,paml.Executable) and x.sink.lookup() in activity.input))
    precedents = {unpin_activity(protocol,x.source.lookup()) for x in flows}
    return precedents

##############################
# Get the protocol
def get_protocol(doc:sbol3.Document):
    # extract set of protocols from document
    protocols = {x for x in doc.objects if isinstance(x, paml.Protocol)}
    if len(protocols) == 0:
        raise ValueError("Cannot find any protocols in document")
    elif len(protocols) > 1:
        raise ValueError("Found multiple protocols; don't know which to write")

    # pull the first and only
    return protocols.pop()

##############################
# Serialize order of steps

def serialize_activities(protocol:paml.Protocol):
    serialized_activities = []
    pending_activities = set(protocol.activities)
    while pending_activities:
        non_blocked = {x for x in pending_activities if not (direct_precedents(protocol, x) & set(pending_activities))}
        if not non_blocked:
            raise ValueError("Could not serialize all activities: circular dependency?")
        serialized_activities += non_blocked
        pending_activities -= non_blocked

    assert isinstance(serialized_activities[0], paml.Initial)
    assert isinstance(serialized_activities[-1], paml.Final)

    # filter out control flow statements
    serialized_noncontrol_activities = [x for x in serialized_activities if not isinstance(x, paml.Control)]
    return serialized_noncontrol_activities

##############################
# Write to a markdown file

def write_markdown_file(doc, protocol, serialized_noncontrol_activities, mdc: MarkdownConverter):
    with open(protocol.display_id + '.md', 'w') as file:
        file.write(mdc.markdown_header(protocol))

        file.write('\n\n## Materials\n')
        for material in protocol.material:
            file.write(markdown_material(material.lookup(), mdc))
        for container in (x for x in protocol.locations if isinstance(x, paml.Container)):
            file.write(markdown_container_toplevel(container, mdc))

        file.write('\n\n## Steps\n')
        for step in range(len(serialized_noncontrol_activities)):
            file.write('### Step ' + str(step + 1) + '\n' + serialized_noncontrol_activities[step].to_markdown(mdc) + '\n')

        # make sure the file is fully written
        file.flush()


##############################
# Write to an accompanying Excel file

def excel_container_name(container):
   return (container.display_id if (container.name is None) else container.name)

# def excel_write_container(ws, row_offset, container):
#     return '[' + (container.display_id if (container.name is None) else container.name) + ']('+container.type+')'

def excel_write_containercoodinates(ws, row_offset, col_offset, coordinates, specification_URI):
    fixed_style = ws['A2'].fill
    entry_style = ws['C2'].fill

    # get the column letter
    col = openpyxl.utils.cell.get_column_letter(col_offset+1)
    # make the header
    ws[col+str(row_offset)] = excel_container_name(coordinates.in_container.lookup())
    # write the materials
    block = openpyxl.utils.cell.range_boundaries(coordinates.coordinates)
    # use plate coordinates, which are the opposite of excel coordinates
    height = block[2]-block[0]+1
    width = block[3]-block[1]+1
    # write the plate coordinate frame
    for plate_row in range(height):
        coord = col+str(row_offset+plate_row+2)
        ws[coord] = openpyxl.utils.cell.get_column_letter(block[0]+plate_row)
        ws[coord].fill = copy(fixed_style)
    for plate_col in range(width):
        coord = openpyxl.utils.cell.get_column_letter(col_offset+plate_col+2)+str(row_offset+1)
        ws[coord] = str(block[1]+plate_col)
        ws[coord].fill = copy(fixed_style)
    # style the blanks
    for plate_row in range(height):
        for plate_col in range(width):
            coord = openpyxl.utils.cell.get_column_letter(col_offset+plate_col+2)+str(row_offset+plate_row+2)
            ws[coord].fill = copy(entry_style)
            ws[coord].alignment = openpyxl.styles.Alignment(horizontal="center")
            plate_coord = openpyxl.utils.cell.get_column_letter(block[0]+plate_row)+str(block[1]+plate_col)
            ws[coord].comment = openpyxl.comments.Comment(coordinates.in_container+"_"+plate_coord+" "+specification_URI, "PAML autogeneration, do not modify", height=24, width=1000)
            ws[coord].protection = openpyxl.styles.Protection(locked=False)

    return (height+2, width+1)

def excel_write_location(ws, row_offset, col_offset, location, specification_URI):
    if isinstance(location, paml.ContainerCoordinates):
        return excel_write_containercoodinates(ws, row_offset, col_offset, location, specification_URI)
    # elif isinstance(location, paml.Container):
    #     return excel_write_container(location)
    else:
        return str(location)

def excel_write_mergedlocations(ws, row_offset, location_spec_list):
    col_offset = 0
    block_height = 0
    while location_spec_list:
        pair = location_spec_list.popitem()
        block = excel_write_location(ws, row_offset, col_offset, pair[0], pair[1])
        col_offset += block[1] + 1
        block_height = max(block_height,block[0])
    return block_height

def excel_write_flow_value(document, value, ws, row_offset):
    if isinstance(value, paml.LocatedData):
        value = value.from_samples  # unwrap value
    if isinstance(value, paml.ReplicateSamples):
        return excel_write_mergedlocations(ws, row_offset, {x.lookup():value.specification for x in value.in_location})
    elif isinstance(value, paml.HeterogeneousSamples):
        return excel_write_mergedlocations(ws, row_offset, {document.find(loc):rep.specification for rep in value.replicate_samples for loc in rep.in_location})
    # if we fall through to here:
    return str(value)


def write_excel_file(doc, protocol, serialized_noncontrol_activities, mdc: MarkdownConverter):
    template_path = posixpath.join(os.path.dirname(os.path.realpath(__file__)),'template.xlsx')
    wb = openpyxl.load_workbook(filename=template_path)
    ws = wb.active  # get the default worksheet

    # write header & metadata
    ws.title = "Data Reporting"
    ws.protection.enable()
    ws['D1'] = protocol.name
    ws['D1'].comment = openpyxl.comments.Comment(protocol.identity, "PAML autogeneration, do not modify", height=24,
                                                 width=1000)
    for row in ws['C2:C4']:
        for cell in row: cell.protection = openpyxl.styles.Protection(locked=False)  # unlock metadata locations
    header_style = ws['A1'].font
    row_offset = 7  # starting point for entries

    # write each value set, incrementing each time
    value_steps = (step for step in range(len(serialized_noncontrol_activities)) if
                   isinstance(serialized_noncontrol_activities[step], paml.Value))
    for step in value_steps:
        coord = 'A' + str(row_offset)
        ws[coord] = 'Report from Step ' + str(step + 1)
        ws[coord].font = copy(header_style)
        value_locations = mdc.protocol_typing.flow_values[serialized_noncontrol_activities[step].input_flows().pop()]
        block_height = excel_write_flow_value(doc, value_locations, ws, row_offset + 1)
        row_offset += block_height + 2

    wb.save(protocol.display_id + '.xlsx')

##############################
# Entry-point for document conversion

# TODO: allow us to control the name of the output
def convert_document(doc:sbol3.Document):
    print('Finding protocol')
    protocol = get_protocol(doc)
    print('Found protocol: '+protocol.display_id)

    print('Inferring flow values')
    protocol_typing = paml.type_inference.ProtocolTyping(protocol)

    mdc = MarkdownConverter(doc,protocol_typing)
    print('Serializing activities')
    serialized_noncontrol_activities = serialize_activities(protocol)

    print('Writing markdown file')
    write_markdown_file(doc, protocol, serialized_noncontrol_activities, mdc)

    print('Writing Excel file')
    write_excel_file(doc, protocol, serialized_noncontrol_activities, mdc)

    print('Export complete')



#################################################
# Scraps from elsewhere that will be useful

# # Actually, all of this is more of a forward-looking simulation to be determined later in the .md process itself
# # The type inference can be simpler
# # TODO: generalize to allow multiple containers, non-identical locations
# # TODO: track amounts as well
#
# # TODO: this is a kludge that needs to be generalized to handle transfers between non-identical locations
# def translate_sublocation(source: paml.ContainerCoordinates, destination: paml.Container):
#     return paml.ContainerCoordinates(in_location = destination, coordinates = source.coordinates)
#
# def heterogeneous_relocated_samples(self, destination: paml.Location):
#     assert (len(self.containers == 1))
#     relocated = paml.HeterogeneousSamples()
#     relocated.replicate_samples = {r.relocated_samples(translate_sublocation(r.in_location,destination)) for r in self.replicate_samples}
# paml.HeterogeneousSamples.relocated_samples = heterogeneous_relocated_samples
#
# def replicate_relocated_samples(self, destination: paml.Location):
#     assert(len(self.containers==1))
#     relocated = paml.ReplicateSamples(specification=self.specification)
#     relocated.in_location.append(destination)
#     return relocated
# paml.ReplicateSamples.relocated_samples = replicate_relocated_samples
