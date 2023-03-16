import sbol3

import labop

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = "pcr"
sbol3.set_namespace("https://bioprotocols.org/labop/primitives/" + LIBRARY_NAME)


#############################################
# Create the primitives
print("Making primitives for " + LIBRARY_NAME)

p = labop.Primitive("PCR")
p.description = "Specify PCR cycling parameters"
p.add_input("cycles", "http://www.w3.org/2001/XMLSchema#integer")
p.add_input("denaturation_temp", sbol3.OM_MEASURE)
p.add_input("denaturation_time", sbol3.OM_MEASURE)
p.add_input("annealing_temp", sbol3.OM_MEASURE)
p.add_input("annealing_time", sbol3.OM_MEASURE)
p.add_input("extension_temp", sbol3.OM_MEASURE)
p.add_input("extension_time", sbol3.OM_MEASURE)
doc.add(p)

print("Library construction complete")
print("Validating library")
for e in doc.validate().errors:
    print(e)
for w in doc.validate().warnings:
    print(w)

filename = LIBRARY_NAME + ".ttl"
doc.write(filename, "turtle")
print("Library written as " + filename)
