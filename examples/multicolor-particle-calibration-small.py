"""
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
"""
import os

import labop
import sbol3
from tyto import OM
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import (
    MarkdownSpecialization,
)

filename = "".join(__file__.split(".py")[0].split("/")[-1:])

doc = sbol3.Document()
sbol3.set_namespace("http://igem.org/engineering/")

#############################################
# Import the primitive libraries
print("Importing libraries")
labop.import_library("liquid_handling")
print("... Imported liquid handling")
labop.import_library("plate_handling")
print("... Imported plate handling")
labop.import_library("spectrophotometry")
print("... Imported spectrophotometry")
labop.import_library("sample_arrays")
print("... Imported sample arrays")


# create the materials to be provisioned
ddh2o = sbol3.Component("ddH2O", "https://identifiers.org/pubchem.substance:24901740")
ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"

silica_beads = sbol3.Component(
    "silica_beads",
    "https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf",
)
silica_beads.name = "NanoCym 950 nm monodisperse silica nanoparticles"
silica_beads.description = "3e9 NanoCym microspheres/mL ddH20"  # where does this go?

pbs = sbol3.Component("pbs", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341")
pbs.name = "Phosphate Buffered Saline"

fluorescein = sbol3.Component(
    "fluorescein", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341"
)
fluorescein.name = "Fluorescein"

cascade_blue = sbol3.Component(
    "cascade_blue", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341"
)
cascade_blue.name = "Cascade Blue"

sulforhodamine = sbol3.Component(
    "sulforhodamine", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341"
)
sulforhodamine.name = "Sulforhodamine"

doc.add(ddh2o)
doc.add(silica_beads)
doc.add(pbs)
doc.add(fluorescein)
doc.add(cascade_blue)
doc.add(sulforhodamine)


protocol = labop.Protocol("interlab")
protocol.name = "Multicolor fluorescence per bacterial particle calibration"
protocol.version = "1.1b"
protocol.description = """Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)"""
doc.add(protocol)


# Transfer to plate
calibration_plate = protocol.primitive_step(
    "EmptyContainer",
    specification=labop.ContainerSpec(
        "calibration_plate",
        name="calibration plate",
        queryString="cont:Plate96Well",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)


# Perform measurements
read_wells1 = protocol.primitive_step(
    "PlateCoordinates",
    source=calibration_plate.output_pin("samples"),
    coordinates="A1:B12",
)

measure_fluorescence1 = protocol.primitive_step(
    "MeasureFluorescence",
    samples=read_wells1.output_pin("samples"),
    excitationWavelength=sbol3.Measure(488, OM.nanometer),
    emissionWavelength=sbol3.Measure(530, OM.nanometer),
    emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
)
measure_fluorescence1.name = "fluorescein and bead fluorescence"

meta1 = protocol.primitive_step(
    "AttachMetadata",
    data=measure_fluorescence1.output_pin("measurements"),
    metadata=labop.SampleMetadata(
        for_samples=read_wells1.output_pin("samples"), descriptions=""
    ),
)
protocol.designate_output(
    "dataset",
    "http://bioprotocols.org/labop#Dataset",
    source=meta1.output_pin("dataset"),
)


ee = ExecutionEngine(
    specializations=[MarkdownSpecialization(__file__.split(".")[0] + ".md")],
    failsafe=False,
    sample_format="json",
)
execution = ee.execute(
    protocol, sbol3.Agent("test_agent"), id="test_execution", parameter_values=[]
)
print(execution.markdown)

# Dress up the markdown to make it pretty and more readable
execution.markdown = execution.markdown.replace(" milliliter", "mL")
execution.markdown = execution.markdown.replace(" nanometer", "nm")
execution.markdown = execution.markdown.replace(" microliter", "uL")

with open(__file__.split(".")[0] + ".md", "w", encoding="utf-8") as f:
    f.write(execution.markdown)
