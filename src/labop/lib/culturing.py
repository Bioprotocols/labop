import sbol3

import labop

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = "culturing"
sbol3.set_namespace("https://bioprotocols.org/labop/primitives/" + LIBRARY_NAME)

#############################################
# Create the primitives
print("Making primitives for " + LIBRARY_NAME)

p = labop.Primitive("Transform")
p.description = "Transform competent cells."
p.add_input("host", sbol3.SBOL_COMPONENT)
p.add_input("dna", sbol3.SBOL_COMPONENT, unbounded=True)
p.add_input("amount", sbol3.OM_MEASURE, True)  # Can be mass or volume
p.add_input("selection_medium", sbol3.SBOL_COMPONENT)
p.add_input("destination", "http://bioprotocols.org/labop#SampleArray")
p.add_output("transformants", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("Culture")
p.description = "Inoculate and grow cells in a growth medium."
p.add_input("inoculum", sbol3.SBOL_COMPONENT, unbounded=True)
p.add_input(
    "replicates", "http://bioprotocols.org/uml#ValueSpecification", optional=True
)
p.add_input("growth_medium", sbol3.SBOL_COMPONENT)
p.add_input("volume", sbol3.OM_MEASURE, True)
p.add_input("duration", sbol3.OM_MEASURE)
p.add_input("orbital_shake_speed", sbol3.OM_MEASURE, True)  # Should be rpm
p.add_input("temperature", sbol3.OM_MEASURE, True)
p.add_input("container", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("CulturePlates")
p.description = (
    "Create a new sample collection of culture plates using a particular media type"
)
p.add_input("quantity", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("specification", "http://bioprotocols.org/labop#ContainerSpec")
p.add_input(
    "replicates", "http://bioprotocols.org/uml#ValueSpecification", optional=True
)
p.add_input("growth_medium", sbol3.SBOL_COMPONENT)
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("PickColonies")
p.description = (
    "Create a new sample collection of culture plates using a particular media type"
)
p.add_input("colonies", "http://bioprotocols.org/labop#SampleArray")
p.add_input("quantity", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input(
    "replicates", "http://bioprotocols.org/uml#ValueSpecification", optional=True
)
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
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
