"""
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
"""


import os
import sys

if "unittest" in sys.modules:
    REGENERATE_ARTIFACTS = False
else:
    REGENERATE_ARTIFACTS = True

import sbol3
from tyto import OM

import labop
from labop.execution_engine import ExecutionEngine
from labop.strings import Strings
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization

filename = "".join(__file__.split(".py")[0].split("/")[-1:])


NAMESPACE = "http://igem.org/engineering/"
PROTOCOL_NAME = "interlab"
PROTOCOL_LONG_NAME = "Multicolor fluorescence per bacterial particle calibration"


OUT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

if REGENERATE_ARTIFACTS:
    dataset_file = f"{filename}_template"  # name of xlsx
else:
    dataset_file = None

doc = sbol3.Document()
sbol3.set_namespace(NAMESPACE)

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


protocol = labop.Protocol(PROTOCOL_NAME)
protocol.name = PROTOCOL_LONG_NAME
protocol.version = "1.1b"
protocol.description = """Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)"""
doc.add(protocol)


fluorescein_standard_solution_container = protocol.primitive_step(
    "EmptyContainer",
    specification=labop.ContainerSpec(
        "fluroscein_calibrant",
        name="Fluorescein calibrant",
        queryString="cont:StockReagent",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)
fluorescein_standard_solution_container.name = "fluroscein_calibrant"

pbs_container = protocol.primitive_step(
    "EmptyContainer",
    specification=labop.ContainerSpec(
        "pbs_container",
        name="PBS",
        queryString="cont:StockReagent",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)
pbs_container.name = "pbs_container"

provision = protocol.primitive_step(
    "Provision",
    resource=pbs,
    destination=pbs_container.output_pin("samples"),
    amount=sbol3.Measure(5000, OM.microliter),
)
provision = protocol.primitive_step(
    "Provision",
    resource=fluorescein,
    destination=fluorescein_standard_solution_container.output_pin("samples"),
    amount=sbol3.Measure(500, OM.microliter),
)
### Suspend calibrant dry reagents
suspend_fluorescein = protocol.primitive_step(
    "Transfer",
    source=pbs_container.output_pin("samples"),
    destination=fluorescein_standard_solution_container.output_pin("samples"),
    amount=sbol3.Measure(1, OM.millilitre),
)
print(
    f"The reconstituted `{fluorescein.name}` should have a final concentration of 10 uM in `{pbs.name}`."
)
suspend_fluorescein.description = f"The reconstituted `{fluorescein.name}` should have a final concentration of 10 uM in `{pbs.name}`."

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
calibration_plate.name = "calibration_plate"


fluorescein_wells_A1 = protocol.primitive_step(
    "PlateCoordinates",
    source=calibration_plate.output_pin("samples"),
    coordinates="A1",
)

transfer1 = protocol.primitive_step(
    "Transfer",
    source=fluorescein_standard_solution_container.output_pin("samples"),
    destination=fluorescein_wells_A1.output_pin("samples"),
    amount=sbol3.Measure(200, OM.microlitre),
)

blank_wells1 = protocol.primitive_step(
    "PlateCoordinates",
    source=calibration_plate.output_pin("samples"),
    coordinates="A2:D12",
)

transfer_blanks1 = protocol.primitive_step(
    "Transfer",
    source=pbs_container.output_pin("samples"),
    destination=blank_wells1.output_pin("samples"),
    amount=sbol3.Measure(100, OM.microlitre),
)

dilution_series1 = protocol.primitive_step(
    "PlateCoordinates",
    source=calibration_plate.output_pin("samples"),
    coordinates="A1:A11",
)

serial_dilution1 = protocol.primitive_step(
    "SerialDilution",
    source=fluorescein_wells_A1.output_pin("samples"),
    destination=dilution_series1.output_pin("samples"),
    amount=sbol3.Measure(200, OM.microlitre),
    diluent=pbs,
    dilution_factor=2,
    series=10,
)
serial_dilution1.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

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

compute_metadata = protocol.primitive_step(
    "ComputeMetadata", for_samples=read_wells1.output_pin("samples")
)

meta1 = protocol.primitive_step(
    "JoinMetadata",
    dataset=measure_fluorescence1.output_pin("measurements"),
    metadata=compute_metadata.output_pin("metadata"),
)
protocol.designate_output(
    "dataset",
    "http://bioprotocols.org/labop#Dataset",
    source=meta1.output_pin("enhanced_dataset"),
)

if REGENERATE_ARTIFACTS:
    protocol.to_dot().render(os.path.join(OUT_DIR, filename))
    dataset_file = f"{filename}_template"  # name of xlsx
    md_file = filename + ".md"
else:
    dataset_file = None
    md_file = None

ee = ExecutionEngine(
    out_dir=OUT_DIR,
    specializations=[MarkdownSpecialization(md_file, sample_format=Strings.XARRAY)],
    failsafe=False,
    sample_format="xarray",
    dataset_file=dataset_file,
)
execution = ee.execute(
    protocol,
    sbol3.Agent("test_agent"),
    id="test_execution",
    parameter_values=[],
)
print(execution.markdown)

# Dress up the markdown to make it pretty and more readable
execution.markdown = execution.markdown.replace(" milliliter", "mL")
execution.markdown = execution.markdown.replace(" nanometer", "nm")
execution.markdown = execution.markdown.replace(" microliter", "uL")

with open(__file__.split(".")[0] + ".md", "w", encoding="utf-8") as f:
    f.write(execution.markdown)
