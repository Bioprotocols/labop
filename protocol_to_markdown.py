from typing import List, Any

import sbol3
import paml
import tyto

def markdown_measure(measure):
    return str(measure.value) + ' ' + str(tyto.OM.get_term_by_uri(measure.unit))

def markdown_component(component):
    return '[' + (component.display_id if (component.name is None) else component.name) + ']('+component.types[0]+')'

def markdown_container(container):
    return '[' + (container.display_id if (container.name is None) else container.name) + ']('+container.type+')'

def markdown_containercoodinates(coordinates):
    return markdown_container(coordinates.inContainer) + ' ' + coordinates.coordinates

def markdown_location(location):
    if isinstance(location, paml.ContainerCoordinates):
        return markdown_containercoodinates(location)
    elif isinstance(location, paml.Container):
        return markdown_container(location)
    else:
        return str(location)


############
# PROBLEM: the instanceOfPin should be a single field, but is coming through as a list!!!
def input_pin_value(executable, pin_name):
    pin_set = [x for x in executable.input if x.instanceOfPin[0].name == pin_name]
    if len(pin_set) != 1:
        return "[couldn't find input "+pin_name
    pin = pin_set[0]
    if isinstance(pin, paml.LocalValuePin):
        if isinstance(pin.value, paml.Measure):
            return markdown_measure(pin.value)
        elif isinstance(pin.value, sbol3.Component):
            return markdown_component(pin.value)
        elif isinstance(pin.value, paml.Location):
            return markdown_location(pin.value)
        else:
            return str(pin)
    else:
        return str(pin)

def markdown_provision(executable):
    volume = input_pin_value(executable, 'volume')
    resource = input_pin_value(executable, 'resource')
    location = input_pin_value(executable, 'location')
    instruction = 'Pipette '+volume+' of '+resource+' into '+location+'\n'
    return instruction

def markdown_absorbance(executable):
    location = input_pin_value(executable, 'location')
    wavelength = input_pin_value(executable, 'wavelength')
    instruction = 'Measure absorbance of '+location+' at '+wavelength+'\n'
    return instruction

#################
# The IDs on the primitive executables are problematic
primitive_library = {
    'Provision' : markdown_provision,
    'MeasureAbsorbance' : markdown_absorbance
}

def markdown_value(activity):
    flows = (x for x in protocol.hasFlow if (x.sink == activity)) # need to generalize to multiple
    return 'Report values in '+str(next(flows))+'\n'

def markdown_header(protocol):
    header = '# ' + (protocol.display_id if (protocol.name is None) else protocol.name) + '\n'
    header += '\n'
    header += '## Description:\n' + ('No description given' if protocol.description is None else protocol.description) + '\n'
    return header

def markdown_activity(activity):
    if isinstance(activity, paml.PrimitiveExecutable):
        stepwriter = primitive_library[activity.instanceOf.display_id]
        assert stepwriter
        return stepwriter(activity)
    elif isinstance(activity, paml.Value):
        return markdown_value(activity)
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
        owner = next(x for x in protocol.hasActivity if isinstance(x,paml.Executable) and
                     (activity in x.output or activity in protocol.input))
        return owner
    else:
        return activity

def direct_precedents(protocol, activity):
    assert activity in protocol.hasActivity
    flows = (x for x in protocol.hasFlow if (x.sink == activity) or (isinstance(activity,paml.Executable) and x.sink in activity.input))
    precedents = {unpin_activity(protocol,x.source) for x in flows}
    return precedents

##############################
# Get the protocol
print('Reading document')

doc = paml.Document()
doc.read('igem_ludox_draft.json','json-ld')

# extract set of protocols from document
protocols = {x for x in doc.objects if isinstance(x, paml.Protocol)}
if len(protocols)==0:
    raise ValueError("Cannot find any protocols in document")
elif len(protocols)>1:
    raise ValueError("Found multiple protocols; don't know which to write")

# pull the first and only
protocol = protocols.pop()

print('Found protocol: '+protocol.display_id)

##############################
# Serialize order of steps
print('Serializing activities')

serialized_activities = []
pending_activities = set(protocol.hasActivity)
while pending_activities:
    non_blocked = {x for x in pending_activities if not (direct_precedents(protocol,x) &  set(pending_activities))}
    if not non_blocked:
        raise ValueError("Could not serialize all activities: circular dependency?")
        break
    serialized_activities += non_blocked
    pending_activities -= non_blocked

assert isinstance(serialized_activities[0],paml.Initial)
assert isinstance(serialized_activities[-1],paml.Final)

# filter out control flow statements
serialized_noncontrol_activities = [x for x in serialized_activities if not isinstance(x,paml.Control)]

##############################
# Write to a markdown file

print('Writing markdown file')

with open(protocol.display_id+'.md', 'w') as file:
    file.write(markdown_header(protocol))

    file.write('\n\n ## Materials\n')
    for material in protocol.material:
        file.write(markdown_material(material))
    for container in protocol.hasContainer:
        file.write(markdown_container_toplevel(container))

    file.write('\n\n ## Steps\n')
    for step in range(len(serialized_noncontrol_activities)):
        file.write('### Step '+str(step)+'\n'+markdown_activity(serialized_noncontrol_activities[step])+'\n')

    # make sure the file is fully written
    file.flush()

print('Export complete')
