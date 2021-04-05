import sbol3
import paml

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = 'liquid_handling'
sbol3.set_namespace('https://bioprotocols.org/paml/primitives/'+LIBRARY_NAME)


#############################################
# Create the primitives
print('Making primitives for '+LIBRARY_NAME)

p = paml.Primitive('Provision')
p.description = 'Place a measured amount (mass or volume) of a specified component into a location, where it may then be used in executing the protocol.'
p.add_input('component', sbol3.SBOL_COMPONENT)
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('amount', sbol3.OM_MEASURE) # Can be mass or volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, "True")
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Dispense')
p.description = 'Move a measured volume of liquid from one source location to multiple destination locations'
p.add_input('source', 'http://bioprotocols.org/paml#Location')
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('dispenseAmount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, "True")
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Transfer')
p.description = 'Move a measured volume of liquid from an array of source locations to an identically shaped array of destination locations'
p.add_input('source', 'http://bioprotocols.org/paml#Location')
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('dispenseAmount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, "True")
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('PipetteMix')
p.description = 'Mix by cycling a measured volume of liquid in and out at an array of locations a fixed number of times'
p.add_input('source', 'http://bioprotocols.org/paml#Location')
p.add_input('dispenseAmount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, "True")
p.add_input('cycleCount', sbol3.OM_MEASURE, "True")
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

print('Library construction complete')
filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
