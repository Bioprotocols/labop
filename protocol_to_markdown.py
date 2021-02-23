from typing import List, Any

import sbol3
import paml
import tyto

############
# PROBLEM: the instanceOfPin should be a single field, but is coming through as a list!!!
def input_pin_value(executable, pin_name):
    pin = next(x for x in executable.input if x.instanceOfPin[0].name == pin_name)
    return str(pin) # needs to be fixed, obviously

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
    'https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018/PrimitiveExecutable6/Provision' : markdown_provision,
    'https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018/PrimitiveExecutable7/MeasureAbsorbance' : markdown_absorbance
}

def markdown_value(activity):
    return 'Report values in [need to infer location information]\n'

def markdown_header(protocol):
    header = '# ' + (protocol.display_id if (protocol.name is None) else protocol.name) + '\n'
    header += '\n'
    header += '## Description:\n' + ('No description given' if protocol.description is None else protocol.description) + '\n'
    return header

def markdown_activity(activity):
    if isinstance(activity, paml.PrimitiveExecutable):
        stepwriter = primitive_library[activity.instanceOf.identity]
        assert stepwriter
        return stepwriter(activity)
    elif isinstance(activity, paml.Value):
        return markdown_value(activity)
    else:
        raise ValueError("Don't know how to serialize activity "+activity)

def markdown_material(component):
    bullet = '* [' + (component.display_id if (component.name is None) else component.name) + ']('+component.types[0]+')'
    if component.description is not None: bullet += ': ' + component.description
    bullet += '\n'
    return bullet

def markdown_container(container):
    bullet = '* [' + (container.display_id if (container.name is None) else container.name) + ']('+container.type+')'
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
        file.write(markdown_container(container))

    file.write('\n\n ## Steps\n')
    for step in range(len(serialized_noncontrol_activities)):
        file.write('### Step '+str(step)+'\n'+markdown_activity(serialized_noncontrol_activities[step])+'\n')

    # make sure the file is fully written
    file.flush()

print('Export complete')
