"""
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
"""
import json
import os
from urllib.parse import quote

import sbol3
from tyto import OM

import labop
import labop_convert
import uml


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


def generate_protocol(doc: sbol3.Document, activity: labop.Protocol) -> labop.Protocol:
    # create the materials to be provisioned
    dh5alpha = sbol3.Component("dh5alpha", "https://identifiers.org/taxonomy:668369")
    dh5alpha.name = "_E. coli_ DH5 alpha"
    doc.add(dh5alpha)

    lb_cam = sbol3.Component("lb_cam", "")
    lb_cam.name = "LB Broth+chloramphenicol"
    doc.add(lb_cam)

    chloramphenicol = sbol3.Component(
        "chloramphenicol", "https://pubchem.ncbi.nlm.nih.gov/compound/5959"
    )
    chloramphenicol.name = "chloramphenicol"
    doc.add(chloramphenicol)

    neg_control_plasmid = sbol3.Component(
        "neg_control_plasmid", "http://parts.igem.org/Part:BBa_J428100"
    )
    neg_control_plasmid.name = "Negative control 2022"
    neg_control_plasmid.description = "BBa_J428100 Kit Plate 1 Well 12M"

    pos_control_green_plasmid = sbol3.Component(
        "pos_control_green_plasmid", "http://parts.igem.org/Part:BBa_J428112"
    )
    pos_control_green_plasmid.name = "Positive control 2022 Green"
    pos_control_green_plasmid.description = (
        "3_Colors_ins_K2656022 BBa_J428112 Kit Plate 1 Well 14C"
    )

    pos_control_red_plasmid = sbol3.Component(
        "pos_control_red_plasmid", "http://parts.igem.org/Part:BBa_J428101"
    )
    pos_control_red_plasmid.name = "Positive control red (mCherry) Exp 2"
    pos_control_red_plasmid.description = "BBa_J428101 Kit Plate 1 Well 12I"

    test_device1 = sbol3.Component(
        "test_device1", "http://parts.igem.org/Part:BBa_J428106"
    )
    test_device1.name = "Test Device 1 Exp 2 (Dual construct Green and Blue)"
    test_device1.description = "BBa_J428106 Kit Plate 1 Well 12G"

    test_device2 = sbol3.Component(
        "test_device2", "http://parts.igem.org/Part:BBa_J428107"
    )
    test_device2.name = "Test Device 2 Exp 2 (Dual construct Green and Red)"
    test_device2.description = "BBa_J428107 Kit Plate 1 Well 3L"

    test_device3 = sbol3.Component(
        "test_device3", "http://parts.igem.org/Part:BBa_J428105"
    )
    test_device3.name = "Test Device 3 Exp 2 (Dual construct Red and Blue)"
    test_device3.description = "BBa_J428105 Kit Plate 1 Well 5J"

    test_device4 = sbol3.Component(
        "test_device4", "http://parts.igem.org/Part:BBa_J428108"
    )
    test_device4.name = "Test Device 4 Exp 2 (Dual construct Blue and Red)"
    test_device4.description = "BBa_J428108 Kit Plate 1 Well 14E"

    test_device5 = sbol3.Component(
        "test_device5", "http://parts.igem.org/Part:BBa_J428104"
    )
    test_device5.name = "Test Device 5 Exp 2 (Dual construct Red and Green)"
    test_device5.description = "DC_R_ins_K2656022 BBa_J428104 Kit Plate 1 Well 5L"

    doc.add(neg_control_plasmid)
    doc.add(pos_control_green_plasmid)
    doc.add(pos_control_red_plasmid)
    doc.add(test_device1)
    doc.add(test_device2)
    doc.add(test_device3)
    doc.add(test_device4)
    doc.add(test_device5)

    activity.name = "Using the three color calibration protocol: Does the order of transcritional units influence their expression strength?"
    activity.version = sbol3.TextProperty(
        activity,
        "http://igem.org/interlab_working_group#Version",
        0,
        1,
        [],
        "1.0b",
    )
    activity.description = """In this experiment, your team will measure the fluorescence of six devices that encode two fluorescence proteins in two transcriptional units. The devices differ in the order of the transcriptional units. You will calibrate the fluorescence of these devices to the calibrant dyes and the optical density of the culture to the cell density calibrant.

    This experiment aims to assess the lab-to-lab reproducibility of the three color calibration protocol when two fluorescent proteins are expressed in the same cell. Besides this technical question, it also adresses a fundamental synthetic biology question: does the order of the transcritional units (that encode for the two different fluorescent proteins) on the devices influence their expression levels?"""

    activity = doc.find(activity.identity)

    plasmids = [
        neg_control_plasmid,
        pos_control_green_plasmid,
        pos_control_red_plasmid,
        test_device1,
        test_device2,
        test_device3,
        test_device4,
        test_device5,
    ]

    # Day 1: Transformation
    culture_plates = activity.primitive_step(
        "CulturePlates",
        quantity=len(plasmids),
        specification=labop.ContainerSpec(
            "transformant_strains",
            name=f"transformant strains",
            queryString="cont:PetriDish",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
        growth_medium=lb_cam,
    )

    transformation = activity.primitive_step(
        f"Transform",
        host=dh5alpha,
        dna=plasmids,
        selection_medium=lb_cam,
        destination=culture_plates.output_pin("samples"),
    )

    # Day 2: Pick colonies and culture overnight
    culture_container_day1 = activity.primitive_step(
        "ContainerSet",
        quantity=2 * len(plasmids),
        specification=labop.ContainerSpec(
            "culture_day_1",
            name=f"culture (day 1)",
            queryString="cont:CultureTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    overnight_culture = activity.primitive_step(
        "Culture",
        inoculum=transformation.output_pin("transformants"),
        replicates=2,
        growth_medium=lb_cam,
        volume=sbol3.Measure(
            5, OM.millilitre
        ),  # Actually 5-10 ml in the written protocol
        duration=sbol3.Measure(16, OM.hour),  # Actually 16-18 hours
        orbital_shake_speed=sbol3.Measure(
            220, "None"
        ),  # No unit for RPM or inverse minutes
        temperature=sbol3.Measure(37, OM.degree_Celsius),
        container=culture_container_day1.output_pin("samples"),
    )

    # Day 3 culture
    culture_container_day2 = activity.primitive_step(
        "ContainerSet",
        quantity=2 * len(plasmids),
        specification=labop.ContainerSpec(
            "culture_day_2",
            name=f"culture (day 2)",
            queryString="cont:CultureTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    back_dilution = activity.primitive_step(
        "Dilute",
        source=culture_container_day1.output_pin("samples"),
        destination=culture_container_day2.output_pin("samples"),
        replicates=2,
        diluent=lb_cam,
        amount=sbol3.Measure(5.0, OM.millilitre),
        dilution_factor=uml.LiteralInteger(value=10),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )

    # Transfer cultures to a microplate baseline measurement and outgrowth
    timepoint_0hrs = activity.primitive_step(
        "ContainerSet",
        quantity=2 * len(plasmids),
        specification=labop.ContainerSpec(
            "culture_0hr_timepoint",
            name="cultures (0 hr timepoint)",
            queryString="cont:MicrofugeTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    hold = activity.primitive_step(
        "Hold",
        location=timepoint_0hrs.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )
    hold.description = "This will prevent cell growth while transferring samples."

    transfer = activity.primitive_step(
        "Transfer",
        source=culture_container_day2.output_pin("samples"),
        destination=timepoint_0hrs.output_pin("samples"),
        amount=sbol3.Measure(1, OM.milliliter),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )

    baseline_absorbance = activity.primitive_step(
        "MeasureAbsorbance",
        samples=timepoint_0hrs.output_pin("samples"),
        wavelength=sbol3.Measure(600, OM.nanometer),
    )
    baseline_absorbance.name = "baseline absorbance of culture (day 2)"

    conical_tube = activity.primitive_step(
        "ContainerSet",
        quantity=2 * len(plasmids),
        specification=labop.ContainerSpec(
            "back_diluted_culture",
            name=f"back-diluted culture",
            queryString="cont:50mlConicalTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    conical_tube.description = (
        "The conical tube should be opaque, amber-colored, or covered with foil."
    )

    dilution = activity.primitive_step(
        "DiluteToTargetOD",
        source=culture_container_day2.output_pin("samples"),
        destination=conical_tube.output_pin("samples"),
        diluent=lb_cam,
        amount=sbol3.Measure(12, OM.millilitre),
        target_od=sbol3.Measure(0.02, "None"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )  # Dilute to a target OD of 0.2, opaque container
    dilution.description = " Use the provided Excel sheet to calculate this dilution. Reliability of the dilution upon Abs600 measurement: should stay between 0.1-0.9"

    embedded_image = activity.primitive_step(
        "EmbeddedImage",
        image="/Users/bbartley/Dev/git/sd2/labop/fig1_cell_calibration.png",
        caption="Figure 1: Cell Calibration",
    )

    temporary = activity.primitive_step(
        "ContainerSet",
        quantity=2 * len(plasmids),
        specification=labop.ContainerSpec(
            "back_diluted_culture_aliquots",
            name="back-diluted culture aliquots",
            queryString="cont:MicrofugeTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    hold = activity.primitive_step(
        "Hold",
        location=temporary.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )
    hold.description = "This will prevent cell growth while transferring samples."

    transfer = activity.primitive_step(
        "Transfer",
        source=conical_tube.output_pin("samples"),
        destination=temporary.output_pin("samples"),
        amount=sbol3.Measure(1, OM.milliliter),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )

    plate1 = activity.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "plate_1",
            name="plate 1",
            queryString="cont:Plate96Well",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    hold = activity.primitive_step(
        "Hold",
        location=plate1.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )

    plan = labop.SampleData(
        from_samples=timepoint_0hrs.output_pin("samples"),
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
        ),
    )

    transfer = activity.primitive_step(
        "TransferByMap",
        source=timepoint_0hrs.output_pin("samples"),
        destination=plate1.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microliter),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
        plan=plan,
    )
    transfer.description = "See also the plate layout below."

    plate_blanks = activity.primitive_step(
        "Transfer",
        source=[lb_cam],
        destination=plate1.output_pin("samples"),
        coordinates="A1:H1, A10:H10, A12:H12",
        temperature=sbol3.Measure(4, OM.degree_Celsius),
        amount=sbol3.Measure(100, OM.microliter),
    )
    plate_blanks.description = "These samples are blanks."

    embedded_image = activity.primitive_step(
        "EmbeddedImage",
        image="/Users/bbartley/Dev/git/sd2/labop/fig2_cell_calibration.png",
        caption="Figure 2: Cell Calibration",
    )

    # Possibly display map here
    absorbance_plate1 = activity.primitive_step(
        "MeasureAbsorbance",
        samples=plate1.output_pin("samples"),
        wavelength=sbol3.Measure(600, OM.nanometer),
    )
    absorbance_plate1.name = "0 hr absorbance timepoint"
    fluorescence_plate1 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate1.output_pin("samples"),
        excitationWavelength=sbol3.Measure(488, OM.nanometer),
        emissionWavelength=sbol3.Measure(530, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
    )
    fluorescence_plate1.name = "0 hr green fluorescence timepoint"

    fluorescence_blue_plate1 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate1.output_pin("samples"),
        excitationWavelength=sbol3.Measure(405, OM.nanometer),
        emissionWavelength=sbol3.Measure(450, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(50, OM.nanometer),
    )
    fluorescence_blue_plate1.name = "0 hr blue fluorescence timepoint"

    fluorescence_red_plate1 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate1.output_pin("samples"),
        excitationWavelength=sbol3.Measure(561, OM.nanometer),
        emissionWavelength=sbol3.Measure(610, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(20, OM.nanometer),
    )
    fluorescence_red_plate1.name = "0 hr red fluorescence timepoint"

    # Begin outgrowth
    incubate = activity.primitive_step(
        "Incubate",
        location=conical_tube.output_pin("samples"),
        duration=sbol3.Measure(6, OM.hour),
        temperature=sbol3.Measure(37, OM.degree_Celsius),
        shakingFrequency=sbol3.Measure(220, "None"),
    )

    # Hold on ice to inhibit cell growth
    hold = activity.primitive_step(
        "Hold",
        location=timepoint_0hrs.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )
    hold.description = (
        "This will inhibit cell growth during the subsequent pipetting steps."
    )

    # Take a 6hr timepoint measurement
    timepoint_6hrs = activity.primitive_step(
        "ContainerSet",
        quantity=len(plasmids) * 2,
        specification=labop.ContainerSpec(
            "timepoint_6hr",
            name=f"6hr timepoint",
            queryString="cont:MicrofugeTube",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    plate2 = activity.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "plate_2",
            name="plate 2",
            queryString="cont:Plate96Well",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )

    # Hold on ice
    hold = activity.primitive_step(
        "Hold",
        location=timepoint_6hrs.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )
    hold.description = "This will prevent cell growth while transferring samples."

    hold = activity.primitive_step(
        "Hold",
        location=plate2.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
    )

    transfer = activity.primitive_step(
        "Transfer",
        source=conical_tube.output_pin("samples"),
        destination=timepoint_6hrs.output_pin("samples"),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
        amount=sbol3.Measure(1, OM.milliliter),
    )

    plan = labop.SampleData(
        from_samples=timepoint_6hrs.output_pin("samples"),
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
        ),
    )

    transfer = activity.primitive_step(
        "TransferByMap",
        source=timepoint_6hrs.output_pin("samples"),
        destination=plate2.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microliter),
        temperature=sbol3.Measure(4, OM.degree_Celsius),
        plan=plan,
    )
    transfer.description = "See the plate layout."

    # Plate the blanks
    plate_blanks = activity.primitive_step(
        "Transfer",
        source=[lb_cam],
        destination=plate2.output_pin("samples"),
        coordinates="A1:H1, A10:H10, A12:H12",
        temperature=sbol3.Measure(4, OM.degree_Celsius),
        amount=sbol3.Measure(100, OM.microliter),
    )
    plate_blanks.description = "These are the blanks."

    endpoint_absorbance_plate2 = activity.primitive_step(
        "MeasureAbsorbance",
        samples=plate2.output_pin("samples"),
        wavelength=sbol3.Measure(600, OM.nanometer),
    )
    endpoint_absorbance_plate2.name = "6 hr absorbance timepoint"

    endpoint_fluorescence_plate2 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate2.output_pin("samples"),
        excitationWavelength=sbol3.Measure(485, OM.nanometer),
        emissionWavelength=sbol3.Measure(530, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
    )
    endpoint_fluorescence_plate2.name = "6 hr green fluorescence timepoint"

    endpoint_fluorescence_blue_plate2 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate2.output_pin("samples"),
        excitationWavelength=sbol3.Measure(405, OM.nanometer),
        emissionWavelength=sbol3.Measure(450, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(50, OM.nanometer),
    )
    endpoint_fluorescence_blue_plate2.name = "6 hr blue fluorescence timepoint"

    endpoint_fluorescence_red_plate2 = activity.primitive_step(
        "MeasureFluorescence",
        samples=plate2.output_pin("samples"),
        excitationWavelength=sbol3.Measure(561, OM.nanometer),
        emissionWavelength=sbol3.Measure(610, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(20, OM.nanometer),
    )
    endpoint_fluorescence_red_plate2.name = "6 hr red fluorescence timepoint"

    activity.designate_output(
        "baseline_absorbance_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=baseline_absorbance.output_pin("measurements"),
    )
    activity.designate_output(
        "absorbance_plate1_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=absorbance_plate1.output_pin("measurements"),
    )
    activity.designate_output(
        "fluorescence_plate1_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=fluorescence_plate1.output_pin("measurements"),
    )
    activity.designate_output(
        "fluorescence_blue_plate1_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=fluorescence_blue_plate1.output_pin("measurements"),
    )
    activity.designate_output(
        "fluorescence_red_plate1_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=fluorescence_red_plate1.output_pin("measurements"),
    )

    activity.designate_output(
        "endpoint_absorbance_plate2_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=endpoint_absorbance_plate2.output_pin("measurements"),
    )
    activity.designate_output(
        "endpoint_fluorescence_plate2_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=endpoint_fluorescence_plate2.output_pin("measurements"),
    )
    activity.designate_output(
        "endpoint_fluorescence_blue_plate2_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=endpoint_fluorescence_blue_plate2.output_pin("measurements"),
    )
    activity.designate_output(
        "endpoint_fluorescence_red_plate2_measurements",
        "http://bioprotocols.org/labop#SampleData",
        source=endpoint_fluorescence_red_plate2.output_pin("measurements"),
    )

    return activity


class InterlabCustomSpecialization(labop.execution.harness.ProtocolSpecialization):
    def generate_artifact(self, harness: "ProtocolHarness"):
        execution = self.specialization.execution

        # Post-process the markdown to add a table that shows where each
        # iGEM part is contained in the parts distribution kit
        render_kit_coordinates_table(execution)

        print(execution.markdown)
        execution.markdown = execution.markdown.replace("`_E. coli_", "_`E. coli`_ `")
        super().generate_artifact(harness)


if __name__ == "__main__":
    harness = labop.execution.harness.ProtocolHarness(
        protocol_name="interlab",
        clean_output=True,
        base_dir=os.path.join(os.path.dirname(__file__), "out", "out_igem_example2"),
        entry_point=generate_protocol,
        agent="test_agent",
        libraries=[
            "liquid_handling",
            "plate_handling",
            "spectrophotometry",
            "sample_arrays",
            "culturing",
        ],
        artifacts=[
            InterlabCustomSpecialization(
                specialization=labop_convert.MarkdownSpecialization(
                    "test_LUDOX_markdown.md"
                )
            )
        ],
        execution_kwargs={
            "failsafe": False,
            "sample_format": "json",
            "track_samples": False,
        },
        execution_id="test_execution",
    )
    harness.run()
