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
p.add_input('resource', sbol3.SBOL_COMPONENT)
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('amount', sbol3.OM_MEASURE) # Can be mass or volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Dispense')
p.description = 'Move a measured volume of liquid from one source sample to create samples at multiple destination locations'
p.add_input('source', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('amount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Transfer')
p.description = 'Move a measured volume of from an array of source samples to an identically shaped array in a destination locations'
p.add_input('source', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('destination', 'http://bioprotocols.org/paml#Location')
p.add_input('amount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('PipetteMix')
p.description = 'Mix by cycling a measured volume of liquid in and out at an array of samples a fixed number of times'
p.add_input('samples', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('amount', sbol3.OM_MEASURE) # Must be volume
p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
p.add_input('cycleCount', sbol3.OM_MEASURE, True)
doc.add(p)

print('Library construction complete')

print('Validating library')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
