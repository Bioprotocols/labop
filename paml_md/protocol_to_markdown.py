import sbol3
import paml
import tyto
import openpyxl
import os
import posixpath
import paml.type_inference
from copy import copy

def markdown_measure(measure):
    return str(measure.value) + ' ' + str(tyto.OM.get_term_by_uri(measure.unit))

def markdown_component(component):
    return '[' + (component.display_id if (component.name is None) else component.name) + ']('+component.types[0]+')'

def markdown_container(container):
    return '[' + (container.display_id if (container.name is None) else container.name) + ']('+container.type+')'

def markdown_containercoodinates(coordinates):
    return markdown_container(coordinates.in_container.lookup()) + ' ' + coordinates.coordinates

def markdown_location(location):
    if isinstance(location, paml.ContainerCoordinates):
        return markdown_containercoodinates(location)
    elif isinstance(location, paml.Container):
        return markdown_container(location)
    else:
        return str(location)

def markdown_mergedlocations(location_list):
    this = markdown_location(location_list.pop())
    if len(location_list) == 0:
        return this
    if len(location_list) == 1:
        return this + ' and ' + markdown_mergedlocations(location_list)
    else:
        return this + ', ' + markdown_mergedlocations(location_list)

def markdown_flow_value(document, value):
    if isinstance(value, paml.ReplicateSamples):
        return markdown_mergedlocations({x.lookup() for x in value.in_location})
    elif isinstance(value, paml.HeterogeneousSamples):
        return markdown_mergedlocations({document.find(loc) for rep in value.replicate_samples for loc in rep.in_location})
    # if we fall through to here:
    return str(value)


############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def input_pin_value(document, protocol, executable, pin_name):
    pin_set = [x for x in executable.input if document.find(x.instance_of).name == pin_name]
    if len(pin_set) != 1:
        return "[couldn't find input "+pin_name+"]"
    pin = pin_set[0]
    if isinstance(pin, paml.LocalValuePin):
        if isinstance(pin.value, sbol3.Measure):
            return markdown_measure(pin.value)
    elif isinstance(pin, paml.ReferenceValuePin):
        value = pin.value.lookup()
        if isinstance(value, sbol3.Component):
            return markdown_component(value)
        elif isinstance(value, paml.Location):
            return markdown_location(value)
    elif protocol_typing.flow_values[next(x for x in protocol.flows if x.sink.lookup() in executable.input)]:
        value = protocol_typing.flow_values[next(x for x in protocol.flows if x.sink.lookup() in executable.input)]
        print('assigning '+str(value.identity)+" for "+pin.identity)
        return markdown_flow_value(document, value)
    # if we fall through to here:
    return str(pin)

############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def markdown_provision(document, protocol, executable):
    volume = input_pin_value(document, protocol, executable, 'amount')
    resource = input_pin_value(document, protocol, executable, 'resource')
    location = input_pin_value(document, protocol, executable, 'destination')
    instruction = 'Pipette '+volume+' of '+resource+' into '+location+'\n'
    return instruction

############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def markdown_absorbance(document, protocol, executable):
    samples = input_pin_value(document, protocol, executable, 'samples')
    wavelength = input_pin_value(document, protocol, executable, 'wavelength')
    instruction = 'Measure absorbance of '+samples+' at '+wavelength+'\n'
    return instruction

#################
# All this stuff should be transformed into visitor patterns
primitive_library = {
    'https://bioprotocols.org/paml/primitives/liquid_handling/Provision' : markdown_provision,
    'https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance' : markdown_absorbance
}

def get_value_flow_input(protocol, activity):
    flows = (x for x in protocol.flows if (x.sink.lookup() == activity)) # need to generalize to multiple
    return protocol_typing.flow_values[next(flows)]

def markdown_value(document, protocol, activity):
    return 'Report values from '+markdown_flow_value(document, get_value_flow_input(protocol, activity))+'\n'

def markdown_header(protocol):
    header = '# ' + (protocol.display_id if (protocol.name is None) else protocol.name) + '\n'
    header += '\n'
    header += '## Description:\n' + ('No description given' if protocol.description is None else protocol.description) + '\n'
    return header

#############
# BUG: this should not need the document; this is due to pySBOL3 bug #176
def markdown_activity(document, protocol, activity):
    if isinstance(activity, paml.PrimitiveExecutable):
        stepwriter = primitive_library[document.find(activity.instance_of).identity]
        assert stepwriter
        return stepwriter(document, protocol, activity)
    elif isinstance(activity, paml.Value):
        return markdown_value(document, protocol, activity)
    else:
        raise ValueError("Don't know how to serialize activity "+activity)

def markdown_material(component):
    bullet = '* ' + markdown_component(component)
    if component.description is not None: bullet += ': ' + component.description
    bullet += '\n'
    return bullet

def markdown_container_toplevel(container):
    bullet = '* ' + markdown_container(container)
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

def write_markdown_file(doc, protocol, serialized_noncontrol_activities):
    with open(protocol.display_id + '.md', 'w') as file:
        file.write(markdown_header(protocol))

        file.write('\n\n## Materials\n')
        for material in protocol.material:
            file.write(markdown_material(material.lookup()))
        for container in (x for x in protocol.locations if isinstance(x, paml.Container)):
            file.write(markdown_container_toplevel(container))

        file.write('\n\n## Steps\n')
        for step in range(len(serialized_noncontrol_activities)):
            file.write('### Step ' + str(step + 1) + '\n' + markdown_activity(doc, protocol, serialized_noncontrol_activities[
                step]) + '\n')

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
    if isinstance(value, paml.ReplicateSamples):
        return excel_write_mergedlocations(ws, row_offset, {x.lookup():value.specification for x in value.in_location})
    elif isinstance(value, paml.HeterogeneousSamples):
        return excel_write_mergedlocations(ws, row_offset, {document.find(loc):rep.specification for rep in value.replicate_samples for loc in rep.in_location})
    # if we fall through to here:
    return str(value)


def write_excel_file(doc, protocol, serialized_noncontrol_activities):
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
        value_locations = get_value_flow_input(protocol, serialized_noncontrol_activities[step])
        block_height = excel_write_flow_value(doc, value_locations, ws, row_offset + 1)
        row_offset += block_height + 2

    wb.save(protocol.display_id + '.xlsx')

##############################
# Entry-point for document conversion

protocol_typing = None
# TODO: allow us to control the name of the output
def convert_document(doc:sbol3.Document):
    print('Finding protocol')
    protocol = get_protocol(doc)
    print('Found protocol: '+protocol.display_id)

    print('Inferring flow values')
    global protocol_typing # TODO: remove this nasty kludge
    protocol_typing = paml.type_inference.ProtocolTyping(protocol)

    print('Serializing activities')
    serialized_noncontrol_activities = serialize_activities(protocol)

    print('Writing markdown file')
    write_markdown_file(doc, protocol, serialized_noncontrol_activities)

    print('Writing Excel file')
    write_excel_file(doc, protocol, serialized_noncontrol_activities)

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
