"""
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
"""
import json
from urllib.parse import quote

import sbol3
from tyto import OM

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import (
    MarkdownSpecialization,
)


def render_kit_coordinates_table(ex: labop.ProtocolExecution):
    # Get iGEM parts from Document
    components = [
        c
        for c in ex.document.objects
        if type(c) is sbol3.Component and "igem" in c.types[0]
    ]

    # Extract kit coordinates from description, assuming description has the following
    # format: 'BBa_I20270 Kit Plate 1 Well 1A'
    components = [
        (
            c.description.split(" ")[0],  # Part ID
            " ".join(c.description.split(" ")[1:]),
        )  # Kit coordinates
        for c in components
    ]

    # Format markdown table
    table = (
        "#### Table 1: Part Locations in Distribution Kit\n"
        "| Part | Coordinate |\n"
        "| ---- | -------------- |\n"
    )
    for part, coordinate in components:
        table += f"|{part}|{coordinate}|\n"
    table += "\n\n"

    # Insert into markdown document immediately before the Protocol Steps section
    insert_index = ex.markdown.find("## Protocol Steps")
    ex.markdown = ex.markdown[:insert_index] + table + ex.markdown[insert_index:]


filename = "".join(__file__.split(".py")[0].split("/")[-1:])

doc = sbol3.Document()
sbol3.set_namespace("http://igem.org/engineering/")

#############################################
# Import the primitive libraries
print("Importing libraries")
labop.import_library("liquid_handling")
print("... Imported liquid handling")
labop.import_library("plate_handling")
# print('... Imported plate handling')
labop.import_library("spectrophotometry")
print("... Imported spectrophotometry")
labop.import_library("sample_arrays")
print("... Imported sample arrays")
labop.import_library("culturing")
#############################################


# Cells and test circuits
dh5alpha = sbol3.Component("dh5alpha", "https://identifiers.org/taxonomy:668369")
dh5alpha.name = "_E. coli_ DH5 alpha competent cells"
doc.add(dh5alpha)

neg_control_plasmid = sbol3.Component(
    "neg_control_plasmid", "http://parts.igem.org/Part:BBa_J428100"
)
neg_control_plasmid.name = "Negative control"
neg_control_plasmid.description = "BBa_J428100 Kit Plate 1 Well 12M"

pos_control_plasmid = sbol3.Component(
    "pos_control_plasmid", "http://parts.igem.org/Part:BBa_I20270"
)
pos_control_plasmid.name = "Positive control (I20270)"
pos_control_plasmid.description = "BBa_I20270 Kit Plate 1 Well 1A"

test_device1 = sbol3.Component("test_device1", "http://parts.igem.org/Part:BBa_J364000")
test_device1.name = "Test Device 1 (J364000)"
test_device1.description = "BBa_J364000 Kit Plate 1 Well 1C"

test_device2 = sbol3.Component("test_device2", "http://parts.igem.org/Part:BBa_J364001")
test_device2.name = "Test Device 2 (J364001)"
test_device2.description = "BBa_J364001 Kit Plate 1 Well 1E"

test_device3 = sbol3.Component("test_device3", "http://parts.igem.org/Part:BBa_J364002")
test_device3.name = "Test Device 3 (J364002)"
test_device3.description = "BBa_J364002 Kit Plate 1 Well 1G"

test_device4 = sbol3.Component("test_device4", "http://parts.igem.org/Part:BBa_J364007")
test_device4.name = "Test Device 4 (J364007)"
test_device4.description = "BBa_J364007 Kit Plate 1 Well 1I"

test_device5 = sbol3.Component("test_device5", "http://parts.igem.org/Part:BBa_J364008")
test_device5.name = "Test Device 5 (J364008)"
test_device5.description = "BBa_J364008 Kit Plate 1 Well 1K"

test_device6 = sbol3.Component("test_device6", "http://parts.igem.org/Part:BBa_J364009")
test_device6.name = "Test Device 6 (J364009)"
test_device6.description = "BBa_J364009 Kit Plate 1 Well 1M"

doc.add(neg_control_plasmid)
doc.add(pos_control_plasmid)
doc.add(test_device1)
doc.add(test_device2)
doc.add(test_device3)
doc.add(test_device4)
doc.add(test_device5)
doc.add(test_device6)

# Other reagents
lb_cam = sbol3.Component("lb_cam", "")
lb_cam.name = "LB Broth + Chloramphenicol (34 ug/mL)"

lb_agar_cam = sbol3.Component("lb_agar_cam", "")
lb_agar_cam.name = "LB Agar + Chloramphenicol (34 ug/mL)"

chloramphenicol = sbol3.Component(
    "chloramphenicol", "https://pubchem.ncbi.nlm.nih.gov/compound/5959"
)
chloramphenicol.name = "Chloramphenicol stock solution (34 mg/mL)"

ice = sbol3.Component("ice", "")
ice.name = "Ice"

doc.add(lb_cam)
doc.add(lb_agar_cam)
doc.add(chloramphenicol)
doc.add(ice)

# Instruments and laboratory equipment
# TODO: instruments should be represented by sbol3.Agent
plate_reader = sbol3.Component("plate_reader", "")
plate_reader.name = "Plate reader"

shaking_incubator = sbol3.Component("shaking_incubator", "")
shaking_incubator.name = "Shaking incubator"

doc.add(plate_reader)
doc.add(shaking_incubator)


protocol = labop.Protocol("interlab")
protocol.name = "Experiment 3 - Cell measurement protocol Challenge"
protocol.version = sbol3.TextProperty(
    protocol, "http://igem.org/interlab_working_group#Version", 0, 1, [], "1.2b"
)
protocol.description = """This year we plan to test protocols that will eventually be automated. For this reason, we will use 96-well plates instead of test tubes for culturing. Consequently, we want to evaluate how the performance of our plate culturing protocol compares to culturing in test tubes (e.g. 10 mL falcon tube) on a global scale. This version of the interlab protocol involves 2 hr. time interval measurements and incubation inside a microplate reader/incubator.

At the end of the experiment, you will have four plates to be measured. You will measure both fluorescence and absorbance in each plate.

Before performing the cell measurements, you need to perform all the calibration measurements. Please do not proceed unless you have completed the calibration protocol. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Engineering Committee (engineering [at] igem [dot] org) to discuss your situation.

For all below indicated cell measurements, you must use the same type of plates and the same volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same type of plates, volumes, and settings, the measurements will not be valid.

Protocol summary: UPDATE You will transform the eight devices listed in Table 1 into E. coli K-12 DH5-alpha cells. The next day you will pick two colonies from each transformation (16 total) and use them to inoculate 5 mL overnight cultures (this step is still in tubes). Each of these 16 overnight cultures will be used to inoculate four wells in a 96-well plate (200 microliter each, 4 replicates) and one test tube (12 mL). You will measure how fluorescence and optical density develops over 6 hours by taking measurements at time point 0 hour and at time point 6 hours. Follow the protocol below and the visual instructions in Figure 1 and Figure 2."""

doc.add(protocol)
protocol = doc.find(protocol.identity)

plasmids = [
    neg_control_plasmid,
    pos_control_plasmid,
    test_device1,
    test_device2,
    test_device3,
    test_device4,
    test_device5,
    test_device6,
]

# Day 1: Transformation
culture_plates = protocol.primitive_step(
    "CulturePlates",
    quantity=len(plasmids),
    specification=labop.ContainerSpec(
        "transformant_strains",
        name=f"transformant strains",
        queryString="cont:PetriDish",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
    growth_medium=lb_agar_cam,
)

transformation = protocol.primitive_step(
    f"Transform",
    host=dh5alpha,
    dna=plasmids,
    selection_medium=lb_agar_cam,
    destination=culture_plates.output_pin("samples"),
)
transformation.description = "Incubate overnight (for 16 hour) at 37.0 degree Celsius."

# Day 2: Pick colonies and culture overnight
culture_container_day1 = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "culture_day_1",
        name=f"culture (day 1)",
        queryString="cont:CultureTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)

pick_colonies = protocol.primitive_step(
    "PickColonies",
    colonies=transformation.output_pin("transformants"),
    quantity=2 * len(plasmids),
    replicates=2,
)

overnight_culture = protocol.primitive_step(
    "Culture",
    inoculum=pick_colonies.output_pin("samples"),
    replicates=2,
    growth_medium=lb_cam,
    volume=sbol3.Measure(5, OM.millilitre),  # Actually 5-10 ml in the written protocol
    duration=sbol3.Measure(16, OM.hour),  # Actually 16-18 hours
    orbital_shake_speed=sbol3.Measure(220, None),  # No unit for RPM or inverse minutes
    temperature=sbol3.Measure(37, OM.degree_Celsius),
    container=culture_container_day1.output_pin("samples"),
)

# Day 3 culture
culture_container_day2 = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "culture_day_2",
        name=f"culture (day 2)",
        queryString="cont:CultureTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)


back_dilution = protocol.primitive_step(
    "Dilute",
    source=culture_container_day1.output_pin("samples"),
    destination=culture_container_day2.output_pin("samples"),
    replicates=2,
    diluent=lb_cam,
    amount=sbol3.Measure(5.0, OM.millilitre),
    dilution_factor=uml.LiteralInteger(value=10),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)
back_dilution.description = "(This can be also performed on ice)."


# Transfer cultures to a microplate baseline measurement and outgrowth
timepoint_0hrs = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "culture_0hr_timepoint",
        name="cultures (0 hr timepoint)",
        queryString="cont:MicrofugeTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)

hold = protocol.primitive_step(
    "HoldOnIce", location=timepoint_0hrs.output_pin("samples")
)
hold.description = "This will prevent cell growth while transferring samples."

transfer = protocol.primitive_step(
    "Transfer",
    source=culture_container_day2.output_pin("samples"),
    destination=timepoint_0hrs.output_pin("samples"),
    amount=sbol3.Measure(1, OM.milliliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)
transfer.description = "(This can be also performed on Ice)."

# Abs measurement step 11
baseline_absorbance = protocol.primitive_step(
    "MeasureAbsorbance",
    samples=timepoint_0hrs.output_pin("samples"),
    wavelength=sbol3.Measure(600, OM.nanometer),
)
baseline_absorbance.name = "baseline absorbance of culture (day 2)"

# Every measurement primitive produces an output pin called `measurements` that must be designated as a protocol output
protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=baseline_absorbance.output_pin("measurements"),
)


conical_tube = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "back_diluted_culture",
        name=f"back-diluted culture",
        queryString="cont:50mlConicalTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)
conical_tube.description = (
    "The conical tube should be opaque, amber-colored, or covered with foil."
)

dilution = protocol.primitive_step(
    "DiluteToTargetOD",
    source=culture_container_day2.output_pin("samples"),
    destination=conical_tube.output_pin("samples"),
    diluent=lb_cam,
    amount=sbol3.Measure(40, OM.millilitre),
    target_od=sbol3.Measure(0.02, None),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)  # Dilute to a target OD of 0.2, opaque container
dilution.description = f"(This can be also performed on Ice)."

embedded_image = protocol.primitive_step(
    "EmbeddedImage",
    image="fig1_challenge_protocol.png",
    caption="Fig 1: Visual representation of protocol",
)


### Aliquot subcultures for timepoint samples
spec = labop.ContainerSpec(
    "tube1",
    name=f"Tube 1",
    queryString="cont:50mlConicalTube",
    prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
)
timepoint_subculture1 = protocol.primitive_step(
    "ContainerSet", quantity=2 * len(plasmids), specification=spec
)
timepoint_subculture1.description = (
    "The conical tubes should be opaque, amber-colored, or covered with foil."
)

timepoint_subculture2 = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "tube2",
        name=f"Tube 2",
        queryString="cont:50mlConicalTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)
timepoint_subculture2.description = (
    "The conical tubes should be opaque, amber-colored, or covered with foil."
)

timepoint_subculture3 = protocol.primitive_step(
    "ContainerSet",
    quantity=2 * len(plasmids),
    specification=labop.ContainerSpec(
        "tube3",
        name=f"Tube 3",
        queryString="cont:50mlConicalTube",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)
timepoint_subculture3.description = (
    "The conical tubes should be opaque, amber-colored, or covered with foil."
)

transfer = protocol.primitive_step(
    "Transfer",
    source=conical_tube.output_pin("samples"),
    destination=timepoint_subculture1.output_pin("samples"),
    amount=sbol3.Measure(12, OM.milliliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)

transfer = protocol.primitive_step(
    "Transfer",
    source=conical_tube.output_pin("samples"),
    destination=timepoint_subculture2.output_pin("samples"),
    amount=sbol3.Measure(12, OM.milliliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)

transfer = protocol.primitive_step(
    "Transfer",
    source=conical_tube.output_pin("samples"),
    destination=timepoint_subculture3.output_pin("samples"),
    amount=sbol3.Measure(12, OM.milliliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
)

plate1 = protocol.primitive_step(
    "EmptyContainer",
    specification=labop.ContainerSpec(
        "plate1",
        name="plate 1",
        queryString="cont:Plate96Well",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)

hold = protocol.primitive_step("HoldOnIce", location=plate1.output_pin("samples"))

plan = labop.SampleData(
    values=quote(
        json.dumps(
            {
                "1": "A2:D2",
                "2": "E2:H2",
                "3": "A3:D3",
                "4": "E3:H3",
                "5": "A4:D4",
                "6": "E4:H4",
                "7": "A5:D5",
                "8": "E5:H5",
                "9": "A7:D7",
                "10": "E7:H7",
                "11": "A8:D8",
                "12": "E8:H8",
                "13": "A9:D9",
                "14": "E9:H9",
                "15": "A10:D10",
                "16": "E10:H10",
            }
        )
    )
)


transfer = protocol.primitive_step(
    "TransferByMap",
    source=conical_tube.output_pin("samples"),
    destination=plate1.output_pin("samples"),
    amount=sbol3.Measure(200, OM.microliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
    plan=plan,
)
transfer.description = "See the plate layout below."
plate_blanks = protocol.primitive_step(
    "Transfer",
    source=[lb_cam],
    destination=plate1.output_pin("samples"),
    coordinates="A1:H1, A10:H10, A12:H12",
    temperature=sbol3.Measure(4, OM.degree_Celsius),
    amount=sbol3.Measure(200, OM.microliter),
)
plate_blanks.description = "These samples are blanks."

# Display ma here
embedded_image = protocol.primitive_step(
    "EmbeddedImage", image="fig2_cell_calibration.png", caption="Fig 2: Plate layout"
)

absorbance_plate1 = protocol.primitive_step(
    "MeasureAbsorbance",
    samples=plate1.output_pin("samples"),
    wavelength=sbol3.Measure(600, OM.nanometer),
)
absorbance_plate1.name = "0 hr absorbance timepoint"
fluorescence_plate1 = protocol.primitive_step(
    "MeasureFluorescence",
    samples=plate1.output_pin("samples"),
    excitationWavelength=sbol3.Measure(488, OM.nanometer),
    emissionWavelength=sbol3.Measure(530, OM.nanometer),
    emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
)
fluorescence_plate1.name = "0 hr fluorescence timepoint"

protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=absorbance_plate1.output_pin("measurements"),
)
protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=fluorescence_plate1.output_pin("measurements"),
)


# Cover plate
seal = protocol.primitive_step(
    "EvaporativeSeal",
    location=plate1.output_pin("samples"),
    specification=labop.ContainerSpec(
        "seal",
        queryString="cont:MicroplateAdhesiveSealingFilm",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)

############### Hasta aca bien
# Begin outgrowth

incubate = protocol.primitive_step(
    "Incubate",
    location=plate1.output_pin("samples"),
    duration=sbol3.Measure(6, OM.hour),
    temperature=sbol3.Measure(37, OM.degree_Celsius),
    shakingFrequency=sbol3.Measure(220, None),
)

absorbance_plate1 = protocol.primitive_step(
    "MeasureAbsorbance",
    samples=plate1.output_pin("samples"),
    wavelength=sbol3.Measure(600, OM.nanometer),
    timepoints=[
        sbol3.Measure(2, OM.hour),
        sbol3.Measure(4, OM.hour),
        sbol3.Measure(6, OM.hour),
    ],
)

absorbance_plate1.name = "absorbance timepoint"

fluorescence_plate1 = protocol.primitive_step(
    "MeasureFluorescence",
    samples=plate1.output_pin("samples"),
    excitationWavelength=sbol3.Measure(488, OM.nanometer),
    emissionWavelength=sbol3.Measure(530, OM.nanometer),
    emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
    timepoints=[
        sbol3.Measure(2, OM.hour),
        sbol3.Measure(4, OM.hour),
        sbol3.Measure(6, OM.hour),
    ],
)
fluorescence_plate1.name = "fluorescence timepoint"
protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=absorbance_plate1.output_pin("measurements"),
)
protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=fluorescence_plate1.output_pin("measurements"),
)
# Added to si if it changes the next stap
spec.name = "Tube 1"
incubate = protocol.primitive_step(
    "Incubate",
    location=timepoint_subculture1.output_pin("samples"),
    duration=sbol3.Measure(2, OM.hour),
    temperature=sbol3.Measure(37, OM.degree_Celsius),
    shakingFrequency=sbol3.Measure(220, None),
)

# Hold on ice to inhibit cell growth
hold = protocol.primitive_step(
    "HoldOnIce", location=timepoint_subculture1.output_pin("samples")
)
hold.description = "Reserve until the end of the experiment for absorbance and fluorescence measurements."


incubate = protocol.primitive_step(
    "Incubate",
    location=timepoint_subculture2.output_pin("samples"),
    duration=sbol3.Measure(4, OM.hour),
    temperature=sbol3.Measure(37, OM.degree_Celsius),
    shakingFrequency=sbol3.Measure(220, None),
)
hold = protocol.primitive_step(
    "HoldOnIce", location=timepoint_subculture2.output_pin("samples")
)
hold.description = "Reserve until the end of the experiment for absorbance and fluorescence measurements."


incubate = protocol.primitive_step(
    "Incubate",
    location=timepoint_subculture3.output_pin("samples"),
    duration=sbol3.Measure(6, OM.hour),
    temperature=sbol3.Measure(37, OM.degree_Celsius),
    shakingFrequency=sbol3.Measure(220, None),
)
hold = protocol.primitive_step(
    "HoldOnIce", location=timepoint_subculture3.output_pin("samples")
)
hold.description = "Reserve until the end of the experiment for absorbance and fluorescence measurements."


plates234 = protocol.primitive_step(
    "EmptyContainer",
    specification=labop.ContainerSpec(
        "plates234",
        name="Plates 2, 3, and 4",
        queryString="cont:Plate96Well",
        prefixMap={"cont": "https://sift.net/container-ontology/container-ontology#"},
    ),
)

plan = labop.SampleData(
    values=quote(
        json.dumps(
            {
                "1": "A2:D2",
                "2": "E2:H2",
                "3": "A3:D3",
                "4": "E3:H3",
                "5": "A4:D4",
                "6": "E4:H4",
                "7": "A5:D5",
                "8": "E5:H5",
                "9": "A7:D7",
                "10": "E7:H7",
                "11": "A8:D8",
                "12": "E8:H8",
                "13": "A9:D9",
                "14": "E9:H9",
                "15": "A10:D10",
                "16": "E10:H10",
            }
        )
    )
)

spec.name = "Tubes 1, 2 and 3"
transfer = protocol.primitive_step(
    "TransferByMap",
    source=timepoint_subculture1.output_pin("samples"),
    destination=plates234.output_pin("samples"),
    amount=sbol3.Measure(200, OM.microliter),
    temperature=sbol3.Measure(4, OM.degree_Celsius),
    plan=plan,
)


plate_blanks = protocol.primitive_step(
    "Transfer",
    source=[lb_cam],
    destination=plates234.output_pin("samples"),
    coordinates="A1:H1, A10:H10, A12:H12",
    temperature=sbol3.Measure(4, OM.degree_Celsius),
    amount=sbol3.Measure(200, OM.microliter),
)
plate_blanks.description = "These samples are blanks."

absorbance_plate = protocol.primitive_step(
    "MeasureAbsorbance",
    samples=plates234.output_pin("samples"),
    wavelength=sbol3.Measure(600, OM.nanometer),
)
absorbance_plate.name = f"absorbance timepoint"
fluorescence_plate = protocol.primitive_step(
    "MeasureFluorescence",
    samples=plates234.output_pin("samples"),
    excitationWavelength=sbol3.Measure(488, OM.nanometer),
    emissionWavelength=sbol3.Measure(530, OM.nanometer),
    emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
)
fluorescence_plate.name = f"fluorescence timepoint"

protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=absorbance_plate.output_pin("measurements"),
)
protocol.designate_output(
    "measurements",
    "http://bioprotocols.org/labop#SampleData",
    source=fluorescence_plate.output_pin("measurements"),
)


agent = sbol3.Agent("test_agent")
ee = ExecutionEngine(
    specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")],
    failsafe=False,
    sample_format="json",
)
execution = ee.execute(protocol, agent, id="test_execution", parameter_values=[])
render_kit_coordinates_table(execution)
print(execution.markdown)

# Dress up the markdown to make it pretty and more readable
execution.markdown = execution.markdown.replace("`_E. coli_", "_`E. coli`_ `")
execution.markdown = execution.markdown.replace(" milliliter", "mL")
execution.markdown = execution.markdown.replace(
    " degree Celsius", "\u00B0C"
)  # degree symbol
execution.markdown = execution.markdown.replace(" nanometer", "nm")
execution.markdown = execution.markdown.replace(" microliter", "uL")

with open(filename + ".md", "w", encoding="utf-8") as f:
    f.write(execution.markdown)
