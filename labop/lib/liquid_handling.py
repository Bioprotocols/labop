import sbol3

import labop

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = "liquid_handling"
sbol3.set_namespace("https://bioprotocols.org/labop/primitives/" + LIBRARY_NAME)

#############################################
# Create the primitives
print("Making primitives for " + LIBRARY_NAME)

p = labop.Primitive("Provision")
p.description = "Place a measured amount (mass or volume) of a specified component into a location, where it may then be used in executing the protocol."
p.add_input("resource", sbol3.SBOL_COMPONENT)
p.add_input(
    "destination", "http://bioprotocols.org/labop#SampleCollection"
)  # TODO: change these URIs to constants on resolution of pySBOL issue #228
p.add_input("amount", sbol3.OM_MEASURE)  # Can be mass or volume
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("Dispense")
p.description = "Move a measured volume of liquid from one source sample to create samples at multiple destination locations"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("Transfer")
p.description = "Move a measured volume taken from a collection of source samples to a location whose shape can contain them in a destination locations"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input(
    "coordinates",
    "http://bioprotocols.org/uml#ValueSpecification",
    optional=True,
)
p.add_input(
    "replicates",
    "http://bioprotocols.org/uml#ValueSpecification",
    optional=True,
)
p.add_input("temperature", sbol3.OM_MEASURE, optional=True)
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("TransferInto")
p.description = "Mix a measured volume taken from an collection of source samples into a collection of destination samples whose shape can contain them"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("mixCycles", sbol3.OM_MEASURE, True)
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("Dilute")
p.description = "Dilute"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("diluent", sbol3.SBOL_COMPONENT)
p.add_input(
    "replicates",
    "http://bioprotocols.org/uml#ValueSpecification",
    optional=True,
)
p.add_input("dilution_factor", sbol3.OM_MEASURE)
p.add_input("temperature", sbol3.OM_MEASURE, optional=True)
doc.add(p)

p = labop.Primitive("DiluteToTargetOD")
p.description = "Dilute"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("diluent", sbol3.SBOL_COMPONENT)
p.add_input("target_od", sbol3.OM_MEASURE)
p.add_input("temperature", sbol3.OM_MEASURE)
doc.add(p)

p = labop.Primitive("SerialDilution")
p.description = "Serial Dilution"
p.add_input("samples", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("direction", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("diluent", sbol3.SBOL_COMPONENT)
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
doc.add(p)


p = labop.Primitive("TransferByMap")
p.description = "Move volumes from a collection of source samples to a collection of destination samples following a plan of value given for each location"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleCollection")
p.add_input(
    "plan", "http://bioprotocols.org/labop#SampleData"
)  # Must be a set of component/volume values
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("temperature", sbol3.OM_MEASURE)
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("PipetteMix")
p.description = "Mix by cycling a measured volume of liquid in and out at an array of samples a fixed number of times"
p.add_input("samples", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
p.add_input("dispenseVelocity", sbol3.OM_MEASURE, True)
p.add_input("cycleCount", sbol3.OM_MEASURE, True)
doc.add(p)

p = labop.Primitive("Vortex")
p.description = "Vortex a sample in order to homogeneously mix or suspend its contents"
p.add_input("samples", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("duration", sbol3.OM_MEASURE)  # Must be time
doc.add(p)

p = labop.Primitive("Discard")
p.description = "Discard part or all of a sample"
p.add_input("samples", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("amount", sbol3.OM_MEASURE)  # Must be volume
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
