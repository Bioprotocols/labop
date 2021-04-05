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
p.description = 'Cover a location to keep materials from entering or exiting'
p.add_input('location', 'http://bioprotocols.org/paml#Location')
p.add_input('type', 'http://www.w3.org/2001/XMLSchema#anyURI')
doc.add(p)

p = paml.Primitive('Seal')
p.description = 'Seal a location to guarantee isolation from the external environment'
p.add_input('location', 'http://bioprotocols.org/paml#Location')
p.add_input('type', 'http://www.w3.org/2001/XMLSchema#anyURI') # e.g., breathable vs. non-breathable
p.add_input('method', 'http://www.w3.org/2001/XMLSchema#anyURI') # e.g., thermal vs. adhesive
doc.add(p)

p = paml.Primitive('Uncover')
p.description = 'Uncover a location to allow materials to enter or exit'
p.add_input('location', 'http://bioprotocols.org/paml#Location')
doc.add(p)

p = paml.Primitive('Unseal')
p.description = 'Unseal a sealed location to break its isolation from the external environment'
p.add_input('location', 'http://bioprotocols.org/paml#Location')
doc.add(p)

p = paml.Primitive('Incubate')
p.description = 'Incubate a sample under specified conditions for a fixed period of time'
p.add_input('location', 'http://bioprotocols.org/paml#Location')
p.add_input('duration', sbol3.OM_MEASURE) # time
p.add_input('temperature', sbol3.OM_MEASURE) # temperature
p.add_input('shakingFrequency', sbol3.OM_MEASURE, 'True') # Hertz
doc.add(p)

print('Library construction complete')
filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
