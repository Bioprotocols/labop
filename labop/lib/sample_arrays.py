import sbol3

import labop

#############################################
# Set up the document
doc = sbol3.Document()
LIBRARY_NAME = "sample_arrays"
sbol3.set_namespace("https://bioprotocols.org/labop/primitives/" + LIBRARY_NAME)


#############################################
# Create the primitives
print("Making primitives for " + LIBRARY_NAME)

# TODO need a Container primitive, with empty container as special case.
p = labop.Primitive("EmptyContainer")
p.description = "Allocate a sample array with size and type based on an empty container"
p.add_input("specification", sbol3.SBOL_IDENTIFIED)
p.add_input("sample_array", "http://bioprotocols.org/labop#SampleArray", optional=True)
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("PlateCoordinates")
p.description = "Select only the samples with specified row/column combination from a sample collection"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("coordinates", "http://bioprotocols.org/uml#ValueSpecification")
p.add_output("samples", "http://bioprotocols.org/labop#SampleCollection")
doc.add(p)

p = labop.Primitive("Rows")
p.description = "Select only the samples with specified rows from a sample collection"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("row", "http://bioprotocols.org/uml#ValueSpecification")
p.add_output("samples", "http://bioprotocols.org/labop#SampleCollection")
doc.add(p)

p = labop.Primitive("Columns")
p.description = (
    "Select only the samples with specified columns from a sample collection"
)
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("col", "http://bioprotocols.org/uml#ValueSpecification")
p.add_output("samples", "http://bioprotocols.org/labop#SampleCollection")
doc.add(p)

p = labop.Primitive("ReplicateCollection")
p.description = "Create a new sample collection containing a set of replicate slots for every sample in the input"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("replicates", "http://bioprotocols.org/uml#ValueSpecification")
p.add_output("samples", "http://bioprotocols.org/labop#SampleCollection")
doc.add(p)

p = labop.Primitive("DuplicateCollection")
p.description = (
    "Create a new sample collection with identical parameters to the input collection"
)
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_output("samples", "http://bioprotocols.org/labop#SampleCollection")
doc.add(p)

p = labop.Primitive("StockReagent")
p.description = "Allocate a SampleArray object representing a stock reagent"
p.add_input("initial_contents", sbol3.SBOL_IDENTIFIED)
p.add_output("reagent", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("ContainerSet")
p.description = "Create a new sample collection containing a set of replicate slots for every sample in the input"
p.add_input("quantity", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("specification", "http://bioprotocols.org/labop#ContainerSpec")
p.add_input(
    "replicates", "http://bioprotocols.org/uml#ValueSpecification", optional=True
)
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("PoolSamples")
p.description = "Create a new sample collection containing a set of replicate slots for every sample in the input"
p.add_input("source", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("destination", "http://bioprotocols.org/labop#SampleArray")
p.add_input("volume", sbol3.OM_MEASURE)
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("EmbeddedImage")  # This Primitive should move to a separate library
p.add_input("image", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("caption", "http://bioprotocols.org/uml#ValueSpecification")
doc.add(p)

p = labop.Primitive("EmptyRack")
p.description = "Allocate a sample array with dimensions based on a rack as specified by an instance of cont:Rack"
p.add_input("specification", sbol3.SBOL_IDENTIFIED)
p.add_input("sample_array", "http://bioprotocols.org/labop#SampleArray", True)
p.add_output("slots", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("EmptyInstrument")
p.description = (
    "Allocate a sample array with size and type based on the instrument configuration"
)
p.add_input("instrument", "http://www.w3.org/ns/prov#Agent")
p.add_input("sample_array", "http://bioprotocols.org/labop#SampleArray", True)
p.add_output("slots", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)


p = labop.Primitive("LoadContainerInRack")
p.description = "Insert cont:Containers into a rack at the indicated rack coordinates. A call to this Primitive should be preceded by EmptyRack"
p.add_input("slots", "http://bioprotocols.org/labop#SampleCollection")
p.add_input("container", "http://bioprotocols.org/labop#ContainerSpec")
p.add_input("coordinates", "http://bioprotocols.org/uml#ValueSpecification")
p.add_output("samples", "http://bioprotocols.org/labop#SampleMask")
doc.add(p)

p = labop.Primitive("LoadContainerOnInstrument")
p.description = "Insert cont:Containers directly into an instrument, such as a PCR machine, heat block, etc. at the specified slot cooordinates. A call to this Primitive should be preceded by EmptyInstrument"
p.add_input("specification", "http://bioprotocols.org/labop#ContainerSpec")
p.add_input("slots", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("instrument", "http://www.w3.org/ns/prov#Agent")
p.add_output("samples", "http://bioprotocols.org/labop#SampleArray")
doc.add(p)

p = labop.Primitive("LoadRackOnInstrument")
p.description = "Insert a tube rack, pipette tip rack, or microwell plate into an addressed location on a robotic platform"
p.add_input("rack", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input(
    "coordinates", "http://bioprotocols.org/uml#ValueSpecification", optional=True
)
doc.add(p)

p = labop.Primitive("ConfigureRobot")
p.description = "Specify an instrument configuration consisting of optional instrument modules, such as pipettes, heat blocks, thermocyclers, etc, which are represented by Agents"
p.add_input("instrument", "http://www.w3.org/ns/prov#Agent")
p.add_input("mount", "http://bioprotocols.org/uml#ValueSpecification", optional=True)
doc.add(p)

p = labop.Primitive("JoinMetadata")
p.description = "Associate a labop:SampleMetadata with a labop.Dataset to create a labop.Dataset that also includes the new metadata"
p.add_input("metadata", "http://bioprotocols.org/labop#SampleMetadata")
p.add_input("dataset", "http://bioprotocols.org/labop#Dataset"),
p.add_output("enhanced_dataset", "http://bioprotocols.org/labop#Dataset")
doc.add(p)

p = labop.Primitive("JoinDatasets")
p.description = "Group several labop.Dataset to create a labop.Dataset"
p.add_input("metadata", "http://bioprotocols.org/labop#SampleMetadata", optional=True)
p.add_input("dataset", "http://bioprotocols.org/labop#Dataset", unbounded=True),
p.add_output("joint_dataset", "http://bioprotocols.org/labop#Dataset")
doc.add(p)

p = labop.Primitive("ExcelMetadata")
p.description = "Parse sample descriptions and metadata from an Excel file"
p.add_input("filename", "http://bioprotocols.org/uml#ValueSpecification")
p.add_input("for_samples", "https://bioprotocols.org/labop#SampleArray")
p.add_output("metadata", "http://bioprotocols.org/labop#SampleMetadata")
doc.add(p)

p = labop.Primitive("ComputeMetadata")
p.description = (
    "Compute Metadata describing samples at the time that this primitive executes."
)
p.add_input("for_samples", "https://bioprotocols.org/labop#SampleArray")
p.add_output("metadata", "http://bioprotocols.org/labop#SampleMetadata")
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
