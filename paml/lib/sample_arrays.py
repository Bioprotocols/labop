import sbol3
import paml

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = 'sample_arrays'
sbol3.set_namespace('https://bioprotocols.org/paml/primitives/'+LIBRARY_NAME)


#############################################
# Create the primitives
print('Making primitives for '+LIBRARY_NAME)

p = paml.Primitive('EmptyContainer')
p.description = 'Allocate a sample array with size and type based on an empty container'
p.add_input('specification', sbol3.SBOL_IDENTIFIED)
p.add_output('samples', 'http://bioprotocols.org/paml#SampleArray')
doc.add(p)

p = paml.Primitive('PlateCoordinates')
p.description = 'Select only the samples with specified row/column combination from a sample collection'
p.add_input('source', 'http://bioprotocols.org/paml#SampleCollection')
p.add_input('coordinates', 'http://bioprotocols.org/uml#ValueSpecification')
p.add_output('samples', 'http://bioprotocols.org/paml#SampleCollection')
doc.add(p)

p = paml.Primitive('Rows')
p.description = 'Select only the samples with specified rows from a sample collection'
p.add_input('source', 'http://bioprotocols.org/paml#SampleCollection')
p.add_input('row', 'http://bioprotocols.org/uml#ValueSpecification')
p.add_output('samples', 'http://bioprotocols.org/paml#SampleCollection')
doc.add(p)

p = paml.Primitive('Columns')
p.description = 'Select only the samples with specified columns from a sample collection'
p.add_input('source', 'http://bioprotocols.org/paml#SampleCollection')
p.add_input('col', 'http://bioprotocols.org/uml#ValueSpecification')
p.add_output('samples', 'http://bioprotocols.org/paml#SampleCollection')
doc.add(p)

p = paml.Primitive('ReplicateCollection')
p.description = 'Create a new sample collection containing a set of replicate slots for every sample in the input'
p.add_input('source', 'http://bioprotocols.org/paml#SampleCollection')
p.add_input('replicates', 'http://bioprotocols.org/uml#ValueSpecification')
p.add_output('samples', 'http://bioprotocols.org/paml#SampleCollection')
doc.add(p)

p = paml.Primitive('DuplicateCollection')
p.description = 'Create a new sample collection with identical parameters to the input collection'
p.add_input('source', 'http://bioprotocols.org/paml#SampleCollection')
p.add_output('samples', 'http://bioprotocols.org/paml#SampleCollection')
doc.add(p)

print('Library construction complete')

print('Validating library')
for e in doc.validate().errors: print(e);
for w in doc.validate().warnings: print(w);

filename = LIBRARY_NAME+'.ttl'
doc.write(filename,'turtle')
print('Library written as '+filename)
