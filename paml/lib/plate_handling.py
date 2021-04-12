import sbol3
import paml

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = 'plate_handling'
sbol3.set_namespace('https://bioprotocols.org/paml/primitives/'+LIBRARY_NAME)


#############################################
# Create the primitives
print('Making primitives for '+LIBRARY_NAME)

p = paml.Primitive('Cover')
p.description = 'Cover a set of samples to keep materials from entering or exiting'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('type', 'http://www.w3.org/2001/XMLSchema#anyURI')
doc.add(p)

p = paml.Primitive('AdhesiveSeal')
p.description = 'Seal a collection of samples using adhesive to fix the seal, in order to guarantee isolation from the external environment'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('type', 'http://www.w3.org/2001/XMLSchema#anyURI') # e.g., breathable vs. non-breathable
doc.add(p)

p = paml.Primitive('ThermalSeal')
p.description = 'Seal a collection of samples using heat to fix the seal, in order to guarantee isolation from the external environment'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('type', 'http://www.w3.org/2001/XMLSchema#anyURI') # e.g., breathable vs. non-breathable
p.add_input('temperature', sbol3.OM_MEASURE)
p.add_input('duration', sbol3.OM_MEASURE) # length of time to apply the sealing temperature in order to get the seal in place
doc.add(p)

p = paml.Primitive('Uncover')
p.description = 'Uncover a collection of samples to allow materials to enter or exit'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Unseal')
p.description = 'Unseal a sealed collection of samples to break their isolation from the external environment'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
doc.add(p)

p = paml.Primitive('Incubate')
p.description = 'Incubate a set of samples under specified conditions for a fixed period of time'
p.add_input('location', 'http://bioprotocols.org/paml#LocatedSamples')
p.add_input('duration', sbol3.OM_MEASURE) # time
p.add_input('temperature', sbol3.OM_MEASURE) # temperature
p.add_input('shakingFrequency', sbol3.OM_MEASURE, True) # Hertz or RPM?; in either case, defaults to zero
doc.add(p)

print('Library construction complete')
print('Validating library')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
