"""
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import sbol3
from pint import Measurement
from tyto import OM

import labop

NAMESPACE = "http://igem.org/engineering/"
PROTOCOL_NAME = "interlab"
PROTOCOL_LONG_NAME = "Multicolor fluorescence per bacterial particle calibration"

if "unittest" in sys.modules:
    REGENERATE_ARTIFACTS = False
else:
    REGENERATE_ARTIFACTS = True

OUT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

filename = "".join(__file__.split(".py")[0].split("/")[-1:])


def generate_resuspend_subprotocol(doc: sbol3.Document):
    subprotocol = labop.Protocol("Resuspend")
    doc.add(subprotocol)
    source = subprotocol.input_value("source", labop.SampleCollection)
    destination = subprotocol.input_value("destination", labop.SampleCollection)
    amount = subprotocol.input_value("amount", sbol3.Measure)
    suspend_reagent = subprotocol.primitive_step(
        "Transfer", source=source, destination=destination, amount=amount
    )
    vortex = subprotocol.primitive_step(
        "Vortex",
        samples=source,
        duration=sbol3.Measure(30, OM.second),
    )
    subprotocol.order(vortex, subprotocol.final())
    return subprotocol


def generate_protocol():
    import labop

    doc = sbol3.Document()
    sbol3.set_namespace(NAMESPACE)

    #############################################
    # Import the primitive libraries
    # print("Importing libraries")
    labop.import_library("liquid_handling")
    # print("... Imported liquid handling")
    labop.import_library("plate_handling")
    # print("... Imported plate handling")
    labop.import_library("spectrophotometry")
    # print("... Imported spectrophotometry")
    labop.import_library("sample_arrays")
    # print("... Imported sample arrays")

    # create the materials to be provisioned
    ddh2o = sbol3.Component(
        "ddH2O", "https://identifiers.org/pubchem.substance:24901740"
    )
    ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"

    silica_beads = sbol3.Component(
        "silica_beads",
        "https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf",
    )
    silica_beads.name = "NanoCym 950 nm monodisperse silica nanoparticles"
    silica_beads.description = (
        "3e9 NanoCym microspheres/mL ddH20"  # where does this go?
    )

    pbs = sbol3.Component("pbs", "https://pubchem.ncbi.nlm.nih.gov/compound/24978514")
    pbs.name = "Phosphate Buffered Saline"

    fluorescein = sbol3.Component(
        "fluorescein", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341"
    )
    fluorescein.name = "Fluorescein"

    cascade_blue = sbol3.Component(
        "cascade_blue", "https://pubchem.ncbi.nlm.nih.gov/substance/57269662"
    )
    cascade_blue.name = "Cascade Blue"

    sulforhodamine = sbol3.Component(
        "sulforhodamine", "https://pubchem.ncbi.nlm.nih.gov/compound/139216224"
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
    protocol.version = "1.2"
    protocol.description = """
Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)
    """
    doc.add(protocol)

    resuspend_subprotocol = generate_resuspend_subprotocol(doc)

    # Provision an empty Microfuge tube in which to mix the standard solution

    fluorescein_standard_solution_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "fluroscein_calibrant",
            name="Fluorescein calibrant",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    fluorescein_standard_solution_container.name = "fluroscein_calibrant"

    sulforhodamine_standard_solution_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "sulforhodamine_calibrant",
            name="Sulforhodamine 101 calibrant",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    sulforhodamine_standard_solution_container.name = (
        "sulforhodamine_standard_solution_container"
    )

    cascade_blue_standard_solution_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "cascade_blue_calibrant",
            name="Cascade blue calibrant",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    cascade_blue_standard_solution_container.name = (
        "cascade_blue_standard_solution_container"
    )

    microsphere_standard_solution_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "microspheres",
            name="microspheres",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    microsphere_standard_solution_container.name = (
        "microsphere_standard_solution_container"
    )

    ddh2o_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "ddh2o_container",
            name="molecular grade H2O",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    ddh2o_container.name = "ddh2o_container"

    pbs_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "pbs_container",
            name="PBS",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    pbs_container.name = "pbs_container"

    discard_container = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "discard_container",
            name="discard",
            queryString="cont:WasteContainer",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    discard_container.name = "discard_container"

    provision = protocol.primitive_step(
        "Provision",
        resource=ddh2o,
        destination=ddh2o_container.output_pin("samples"),
        amount=sbol3.Measure(12, OM.milliliter),
    )

    provision = protocol.primitive_step(
        "Provision",
        resource=pbs,
        destination=pbs_container.output_pin("samples"),
        amount=sbol3.Measure(12, OM.milliliter),
    )

    provision = protocol.primitive_step(
        "Provision",
        resource=fluorescein,
        destination=fluorescein_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(500, OM.microliter),
    )

    provision = protocol.primitive_step(
        "Provision",
        resource=cascade_blue,
        destination=cascade_blue_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(500, OM.microliter),
    )

    provision = protocol.primitive_step(
        "Provision",
        resource=sulforhodamine,
        destination=sulforhodamine_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(500, OM.microliter),
    )

    provision = protocol.primitive_step(
        "Provision",
        resource=silica_beads,
        destination=microsphere_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(500, OM.microliter),
    )

    ### Suspend calibrant dry reagents
    suspend_fluorescein = protocol.primitive_step(
        resuspend_subprotocol,
        source=pbs_container.output_pin("samples"),
        destination=fluorescein_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(1, OM.millilitre),
    )
    print(
        f"The reconstituted `{fluorescein.name}` should have a final concentration of 10 uM in `{pbs.name}`."
    )
    suspend_fluorescein.description = f"The reconstituted `{fluorescein.name}` should have a final concentration of 10 uM in `{pbs.name}`."

    suspend_sulforhodamine = protocol.primitive_step(
        resuspend_subprotocol,
        source=pbs_container.output_pin("samples"),
        destination=sulforhodamine_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(1, OM.millilitre),
    )
    suspend_sulforhodamine.description = f"The reconstituted `{sulforhodamine.name}` standard will have a final concentration of 2 uM in `{pbs.name}`."

    suspend_cascade_blue = protocol.primitive_step(
        resuspend_subprotocol,
        source=ddh2o_container.output_pin("samples"),
        destination=cascade_blue_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(1, OM.millilitre),
    )
    suspend_cascade_blue.description = f"The reconstituted `{cascade_blue.name}` calibrant will have a final concentration of 10 uM in `{ddh2o.name}`."

    suspend_silica_beads = protocol.primitive_step(
        resuspend_subprotocol,
        source=ddh2o_container.output_pin("samples"),
        destination=microsphere_standard_solution_container.output_pin("samples"),
        amount=sbol3.Measure(1, OM.millilitre),
    )
    suspend_silica_beads.description = f"The resuspended `{silica_beads.name}` will have a final concentration of 3e9 microspheres/mL in `{ddh2o.name}`."

    # Transfer to plate
    calibration_plate = protocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "calibration_plate",
            name="calibration plate",
            queryString="cont:Plate96Well",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    calibration_plate.name = "calibration_plate"

    fluorescein_wells_A1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1",
    )
    fluorescein_wells_B1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="B1",
    )

    sulforhodamine_wells_C1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="C1",
    )
    sulforhodamine_wells_D1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="D1",
    )

    cascade_blue_wells_E1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="E1",
    )
    cascade_blue_wells_F1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="F1",
    )

    silica_beads_wells_G1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="G1",
    )
    silica_beads_wells_H1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="H1",
    )

    # Plate blanks
    blank_wells1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A2:D12",
    )
    blank_wells2 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="E2:H12",
    )
    transfer_blanks1 = protocol.primitive_step(
        "Transfer",
        source=pbs_container.output_pin("samples"),
        destination=blank_wells1.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )

    transfer_blanks2 = protocol.primitive_step(
        "Transfer",
        source=ddh2o_container.output_pin("samples"),
        destination=blank_wells2.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )

    ### Plate calibrants in first column
    transfer1 = protocol.primitive_step(
        "Transfer",
        source=fluorescein_standard_solution_container.output_pin("samples"),
        destination=fluorescein_wells_A1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer2 = protocol.primitive_step(
        "Transfer",
        source=fluorescein_standard_solution_container.output_pin("samples"),
        destination=fluorescein_wells_B1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer3 = protocol.primitive_step(
        "Transfer",
        source=sulforhodamine_standard_solution_container.output_pin("samples"),
        destination=sulforhodamine_wells_C1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer4 = protocol.primitive_step(
        "Transfer",
        source=sulforhodamine_standard_solution_container.output_pin("samples"),
        destination=sulforhodamine_wells_D1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer5 = protocol.primitive_step(
        "Transfer",
        source=cascade_blue_standard_solution_container.output_pin("samples"),
        destination=cascade_blue_wells_E1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer6 = protocol.primitive_step(
        "Transfer",
        source=cascade_blue_standard_solution_container.output_pin("samples"),
        destination=cascade_blue_wells_F1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer7 = protocol.primitive_step(
        "Transfer",
        source=microsphere_standard_solution_container.output_pin("samples"),
        destination=silica_beads_wells_G1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )

    transfer8 = protocol.primitive_step(
        "Transfer",
        source=microsphere_standard_solution_container.output_pin("samples"),
        destination=silica_beads_wells_H1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )

    dilution_series1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1:A11",
    )

    dilution_series2 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="B1:B11",
    )

    dilution_series3 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="C1:C11",
    )

    dilution_series4 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="D1:D11",
    )

    dilution_series5 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="E1:E11",
    )

    dilution_series6 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="F1:F11",
    )

    dilution_series7 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="G1:G11",
    )

    dilution_series8 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="H1:H11",
    )

    discard_coordinates = protocol.primitive_step(
        "PlateCoordinates",
        source=discard_container.output_pin("samples"),
        coordinates="A1",
    )

    serial_dilution1 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series1.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution1.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    embedded_image = protocol.primitive_step(
        "EmbeddedImage",
        image=os.path.join(
            # os.path.dirname(os.path.realpath(__file__)),
            "..",
            "figures",
            "serial_dilution.png",
        ),
        caption="Serial Dilution",
    )

    serial_dilution2 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series2.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution2.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution3 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series3.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution3.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution4 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series4.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution4.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution5 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series5.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution5.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution6 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series6.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution6.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution7 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series7.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution7.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    serial_dilution8 = protocol.primitive_step(
        "SerialDilution",
        samples=dilution_series8.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        direction=labop.Strings.ROW_DIRECTION,
    )
    serial_dilution8.description = "For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously."

    discard_wells = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A11:H11",
    )

    discard = protocol.primitive_step(
        "Transfer",
        source=discard_wells.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        destination=discard_container.output_pin("samples"),
    )

    discard.description = " This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination."

    # Bring to volume of 200 ul
    samples_in_pbs = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1:D12",
    )
    samples_in_ddh2o = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="E1:H12",
    )
    btv1 = protocol.primitive_step(
        "Transfer",
        source=pbs_container.output_pin("samples"),
        destination=samples_in_pbs.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )
    btv1.description = " This will bring all wells to volume 200 microliter."
    btv2 = protocol.primitive_step(
        "Transfer",
        source=ddh2o_container.output_pin("samples"),
        destination=samples_in_ddh2o.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )
    btv2.description = " This will bring all wells to volume 200 microliter."

    # Perform measurements
    read_wells1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1:B12",
    )
    read_wells2 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="C1:D12",
    )
    read_wells3 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="E1:F12",
    )
    read_wells4 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="G1:H12",
    )

    measure_fluorescence1 = protocol.primitive_step(
        "MeasureFluorescence",
        samples=read_wells1.output_pin("samples"),
        excitationWavelength=sbol3.Measure(488, OM.nanometer),
        emissionWavelength=sbol3.Measure(530, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(30, OM.nanometer),
    )
    measure_fluorescence1.name = "fluorescein and bead fluorescence"

    measure_fluorescence2 = protocol.primitive_step(
        "MeasureFluorescence",
        samples=read_wells2.output_pin("samples"),
        excitationWavelength=sbol3.Measure(561, OM.nanometer),
        emissionWavelength=sbol3.Measure(610, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(20, OM.nanometer),
    )
    measure_fluorescence2.name = "sulforhodamine 101 fluorescence"

    measure_fluorescence3 = protocol.primitive_step(
        "MeasureFluorescence",
        samples=read_wells3.output_pin("samples"),
        excitationWavelength=sbol3.Measure(405, OM.nanometer),
        emissionWavelength=sbol3.Measure(450, OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(50, OM.nanometer),
    )
    measure_fluorescence3.name = "cascade blue fluorescence"

    measure_absorbance = protocol.primitive_step(
        "MeasureAbsorbance",
        samples=read_wells4.output_pin("samples"),
        wavelength=sbol3.Measure(600, OM.nanometer),
    )

    # load_excel = protocol.primitive_step(
    #     "ExcelMetadata",
    #     for_samples=calibration_plate.output_pin("samples"),
    #     filename=os.path.join(
    #         os.path.dirname(os.path.realpath(__file__)),
    #         "metadata/sample_metadata.xlsx",
    #     ),
    # )

    # meta1 = protocol.primitive_step(
    #     "JoinMetadata",
    #     dataset=measure_fluorescence1.output_pin("measurements"),
    #     metadata=load_excel.output_pin("metadata"),
    # )

    # meta2 = protocol.primitive_step(
    #     "JoinMetadata",
    #     dataset=measure_fluorescence2.output_pin("measurements"),
    #     metadata=load_excel.output_pin("metadata"),
    # )

    # meta3 = protocol.primitive_step(
    #     "JoinMetadata",
    #     dataset=measure_fluorescence3.output_pin("measurements"),
    #     metadata=load_excel.output_pin("metadata"),
    # )

    # meta4 = protocol.primitive_step(
    #     "JoinMetadata",
    #     dataset=measure_absorbance.output_pin("measurements"),
    #     metadata=load_excel.output_pin("metadata"),
    # )

    # compute_metadata = protocol.primitive_step(
    #    "ComputeMetadata", for_samples=calibration_plate.output_pin("samples")
    # )

    # meta1 = protocol.primitive_step(
    #    "JoinMetadata",
    #    dataset=measure_fluorescence1.output_pin("measurements"),
    #    metadata=compute_metadata.output_pin("metadata"),
    # )

    # meta2 = protocol.primitive_step(
    #    "JoinMetadata",
    #    dataset=measure_fluorescence2.output_pin("measurements"),
    #    metadata=compute_metadata.output_pin("metadata"),
    # )

    # meta3 = protocol.primitive_step(
    #    "JoinMetadata",
    #    dataset=measure_fluorescence3.output_pin("measurements"),
    #    metadata=compute_metadata.output_pin("metadata"),
    # )

    # meta4 = protocol.primitive_step(
    #    "JoinMetadata",
    #    dataset=measure_absorbance.output_pin("measurements"),
    #    metadata=compute_metadata.output_pin("metadata"),
    # )

    # final_dataset = protocol.primitive_step(
    #    "JoinDatasets",
    #    dataset=[
    #        meta1.output_pin("enhanced_dataset"),
    #        meta2.output_pin("enhanced_dataset"),
    #        meta3.output_pin("enhanced_dataset"),
    #        meta4.output_pin("enhanced_dataset"),
    #    ],
    # )
    # outnode = protocol.designate_output(
    #    "dataset",
    #    "http://bioprotocols.org/labop#Dataset",
    #    source=final_dataset.output_pin("joint_dataset"),
    # )

    # protocol.order(final_dataset, protocol.final())
    # protocol.order(outnode, protocol.final())

    if REGENERATE_ARTIFACTS:
        protocol_file = os.path.join(OUT_DIR, f"{filename}-protocol.nt")
        with open(protocol_file, "w") as f:
            print(f"Saving protocol [{protocol_file}].")
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())

    return protocol, doc


def compute_sample_trajectory(protocol, doc):
    import labop
    from labop.execution_engine import ExecutionEngine
    from labop.strings import Strings
    from labop_convert import DefaultBehaviorSpecialization

    if REGENERATE_ARTIFACTS:
        dataset_file = f"{filename}_template"  # name of xlsx
    else:
        dataset_file = None

    ee = ExecutionEngine(
        out_dir=OUT_DIR,
        specializations=[DefaultBehaviorSpecialization()],
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


def generate_markdown_specialization(protocol, doc):
    import labop
    from labop.execution_engine import ExecutionEngine
    from labop.strings import Strings
    from labop_convert import MarkdownSpecialization

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
    md_file = os.path.join(OUT_DIR, filename + ".md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(execution.markdown)

    if REGENERATE_ARTIFACTS:
        with open(os.path.join(OUT_DIR, f"{filename}-execution.nt"), "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())

    # Change dir to get relative references in md file to resolve.
    old_dir = os.getcwd()
    os.chdir(OUT_DIR)

    pandoc = shutil.which("pandoc")
    if pandoc:
        subprocess.run(
            f"{pandoc} {md_file} -o {md_file}.pdf --pdf-engine=xelatex -V geometry:margin=1in -V linkcolor:blue",
            shell=True,
        )

    os.chdir(old_dir)


def generate_ecl_specialization(protocol, doc):
    import labop
    from labop.execution_engine import ExecutionEngine
    from labop.strings import Strings
    from labop_convert import ECLSpecialization

    if REGENERATE_ARTIFACTS:
        ecl_file = filename + ".nb"
    else:
        ecl_file = None

    ee = ExecutionEngine(
        out_dir=OUT_DIR,
        specializations=[ECLSpecialization(ecl_file, sample_format=Strings.XARRAY)],
        failsafe=False,
        sample_format=Strings.XARRAY,
        dataset_file=None,
    )

    execution = ee.execute(
        protocol,
        sbol3.Agent("test_agent"),
        id="test_execution",
        parameter_values=[],
    )
    ecl_file = os.path.join(OUT_DIR, filename)
    with open(ecl_file, "w", encoding="utf-8") as f:
        f.write(execution.markdown)


def generate_autoprotocol_specialization(protocol, doc):
    blockPrint()
    import labop
    from labop.execution_engine import ExecutionEngine
    from labop_convert.autoprotocol.autoprotocol_specialization import (
        AutoprotocolSpecialization,
    )
    from labop_convert.autoprotocol.strateos_api import StrateosAPI, StrateosConfig

    #############################################
    # Autoprotocol and Strateos Configuration
    secrets_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../../secrets/strateos_secrets.json",
    )
    api = StrateosAPI(cfg=StrateosConfig.from_file(secrets_file))

    autoprotocol_output = os.path.join(OUT_DIR, f"{filename}-autoprotocol.json")

    ddh2o = doc.find(f"{NAMESPACE}ddH2O")
    pbs = doc.find(f"{NAMESPACE}pbs")
    fluorescein = doc.find(f"{NAMESPACE}fluorescein")
    cascade_blue = doc.find(f"{NAMESPACE}cascade_blue")
    sulforhodamine = doc.find(f"{NAMESPACE}sulforhodamine")
    silica_beads = doc.find(f"{NAMESPACE}silica_beads")
    discard_container = [x for x in protocol.nodes if x.name == "discard_container"][0]
    fluorescein_standard_solution_container = [
        x for x in protocol.nodes if x.name == "fluroscein_calibrant"
    ][0]
    sulforhodamine_standard_solution_container = [
        x
        for x in protocol.nodes
        if x.name == "sulforhodamine_standard_solution_container"
    ][0]
    cascade_blue_standard_solution_container = [
        x
        for x in protocol.nodes
        if x.name == "cascade_blue_standard_solution_container"
    ][0]
    microsphere_standard_solution_container = [
        x for x in protocol.nodes if x.name == "microsphere_standard_solution_container"
    ][0]
    ddh2o_container = [x for x in protocol.nodes if x.name == "ddh2o_container"][0]
    pbs_container = [x for x in protocol.nodes if x.name == "pbs_container"][0]
    calibration_plate = [x for x in protocol.nodes if x.name == "calibration_plate"][0]

    resolutions = {
        ddh2o.identity: "rs1aquf68bkbz2",
        pbs.identity: "rs1aquf68bkbz2",
        fluorescein.identity: "rs194na2u3hfam",  # LUDOX
        cascade_blue.identity: "rs1b6z2vgatkq7",  # LUDOX
        sulforhodamine.identity: "rs1bga8d55vfz5",  # Texas Red
        silica_beads.identity: "rs1b6z2vgatkq7",  # LUDOX
        discard_container.input_pin("specification").identity: "ct1awysukrf9dq8ryt",
        fluorescein_standard_solution_container.input_pin(
            "specification"
        ).identity: "ct1awyw7ggr8vmkc9v",
        sulforhodamine_standard_solution_container.input_pin(
            "specification"
        ).identity: "ct1awywckw2fh6uh3d",
        cascade_blue_standard_solution_container.input_pin(
            "specification"
        ).identity: "ct1awywedd5gg2fz29",
        microsphere_standard_solution_container.input_pin(
            "specification"
        ).identity: "ct1awywfwwbdwfvqpv",
        ddh2o_container.input_pin("specification").identity: "ct1awywhcqqcy22jj2",
        pbs_container.input_pin("specification").identity: "ct1awywjusyasfcfa7",
        calibration_plate.input_pin("specification").identity: "ct1awywnhz89jfjsgt",
    }
    autoprotocol_specialization = AutoprotocolSpecialization(
        autoprotocol_output, api, resolutions=resolutions
    )

    ee = ExecutionEngine(specializations=[autoprotocol_specialization], failsafe=False)
    execution = ee.execute(
        protocol,
        sbol3.Agent("test_agent"),
        id="test_execution",
        parameter_values=[],
    )

    enablePrint()

    print(f"Saving Autoprotocol [{autoprotocol_output}].")

    print(f"Analyzing Protocol ...")

    st = api.get_strateos_connection()
    response = st.analyze_run(autoprotocol_specialization.protocol, test_mode=True)

    # # Dress up the markdown to make it pretty and more readable
    # execution.markdown = execution.markdown.replace(' milliliter', 'mL')
    # execution.markdown = execution.markdown.replace(' nanometer', 'nm')
    # execution.markdown = execution.markdown.replace(' microliter', 'uL')

    if REGENERATE_ARTIFACTS:
        execution_filename = os.path.join(OUT_DIR, f"{filename}-execution.nt")
        print(f"Saving Execution Record [{execution_filename}]")
        with open(filename, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())


def generate_emeraldcloud_specialization(protocol, doc):
    blockPrint()
    import labop
    from labop.execution_engine import ExecutionEngine
    from labop_convert.emeraldcloud.ecl_specialization import ECLSpecialization

    ecl_output = os.path.join(OUT_DIR, f"{filename}-emeraldcloud.nb")

    ddh2o = doc.find(f"{NAMESPACE}ddH2O")
    pbs = doc.find(f"{NAMESPACE}pbs")
    fluorescein = doc.find(f"{NAMESPACE}fluorescein")
    cascade_blue = doc.find(f"{NAMESPACE}cascade_blue")
    sulforhodamine = doc.find(f"{NAMESPACE}sulforhodamine")
    silica_beads = doc.find(f"{NAMESPACE}silica_beads")
    discard_container = [x for x in protocol.nodes if x.name == "discard_container"][0]
    fluorescein_standard_solution_container = [
        x for x in protocol.nodes if x.name == "fluroscein_calibrant"
    ][0]
    sulforhodamine_standard_solution_container = [
        x
        for x in protocol.nodes
        if x.name == "sulforhodamine_standard_solution_container"
    ][0]
    cascade_blue_standard_solution_container = [
        x
        for x in protocol.nodes
        if x.name == "cascade_blue_standard_solution_container"
    ][0]
    microsphere_standard_solution_container = [
        x for x in protocol.nodes if x.name == "microsphere_standard_solution_container"
    ][0]
    ddh2o_container = [x for x in protocol.nodes if x.name == "ddh2o_container"][0]
    pbs_container = [x for x in protocol.nodes if x.name == "pbs_container"][0]
    calibration_plate = [x for x in protocol.nodes if x.name == "calibration_plate"][0]

    resolutions = {
        ddh2o.identity: "Nuclease-free Water",
        pbs.identity: "1x PBS from 10X stock",
        fluorescein.identity: "1x PBS, 10uM Fluorescein",
        cascade_blue.identity: "1x PBS, 10uM Fluorescein",
        sulforhodamine.identity: "1x PBS, 10uM Fluorescein",
        silica_beads.identity: "Silica beads 2g/ml 950nm",
    }
    ecl_specialization = ECLSpecialization(ecl_output, resolutions=resolutions)

    ee = ExecutionEngine(specializations=[ecl_specialization], failsafe=False)
    execution = ee.execute(
        protocol,
        sbol3.Agent("test_agent"),
        id="test_execution",
        parameter_values=[],
    )

    enablePrint()

    print(f"Saving EmeraldCloud [{ecl_output}].")

    print(f"Analyzing Protocol ...")

    if REGENERATE_ARTIFACTS:
        execution_filename = os.path.join(OUT_DIR, f"{filename}-execution.nt")
        print(f"Saving Execution Record [{execution_filename}]")
        with open(filename, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())


def test_autoprotocol():
    from labop_convert.autoprotocol.strateos_api import StrateosAPI, StrateosConfig

    secrets_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../../secrets/strateos_secrets.json",
    )
    api = StrateosAPI(cfg=StrateosConfig.from_file(secrets_file))

    ap_file = os.path.join(OUT_DIR, f"{filename}-autoprotocol.json")
    st = api.get_strateos_connection()
    with open(ap_file, "r") as ap:
        response = st.submit_run(
            json.loads(ap.read()),
            project_id=api.cfg.project_id,
            title=PROTOCOL_LONG_NAME,
            test_mode=True,
        )
    print(f"Received response:\n{response}")

    launch_confirmation = os.path.join(
        OUT_DIR, f"{filename}-strateos-launch-confirmation.json"
    )

    with open(launch_confirmation, "w") as lconf:
        print(f"Saving Launch Confirmation [{launch_confirmation}].")
        lconf.write(json.dumps(response))


def read_protocol(filename=os.path.join(OUT_DIR, f"{filename}-protocol.nt")):
    import labop

    doc = sbol3.Document()
    sbol3.set_namespace(NAMESPACE)

    doc.read(filename, "nt")
    protocol = doc.find(f"{NAMESPACE}{PROTOCOL_NAME}")

    return protocol, doc


# Disable
def blockPrint():
    pass
    # sys.stdout = open(os.devnull, "w")


# Restore
def enablePrint():
    sys.stdout = sys.__stdout__


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g",
        "--generate-protocol",
        default=False,
        action="store_true",
        help=f"Generate the artifacts/{filename}-protocol.nt LabOP protocol file.",
    )
    parser.add_argument(
        "-c",
        "--compute-sample-trajectory",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the sample trajectory of the LabOP protocol.",
    )
    parser.add_argument(
        "-m",
        "--generate-markdown",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the artifacts/{filename}.md Markdown specialization of the LabOP protocol.",
    )
    parser.add_argument(
        "-a",
        "--generate-autoprotocol",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the artifacts/{filename}-autoprotocol.json Autoprotocol specialization of the LabOP protocol.",
    )

    parser.add_argument(
        "-t",
        "--test-autoprotocol",
        default=False,
        action="store_true",
        help=f"Submit the artifacts/{filename}-autoprotocol.json Autoprotocol file to the Strateos run queue.",
    )
    parser.add_argument(
        "-e",
        "--generate-emeraldcloud",
        default=True,
        action="store_true",
        help=f"Execute the protocol to generate the Emerald Cloud notebook at artifacts/{filename}-emeraldcloud.nb.",
    )
    args = parser.parse_args()

    if args.generate_protocol or not os.path.exists(
        os.path.join(OUT_DIR, filename + "-protocol.nt")
    ):
        print("Generating Protocol ...")
        protocol, doc = generate_protocol()

    if args.compute_sample_trajectory:
        compute_sample_trajectory(*read_protocol())

    if args.generate_markdown:
        print("Generating Markdown ...")
        generate_markdown_specialization(*read_protocol())

    if args.generate_autoprotocol:
        print("Generating Autoprotocol ...")
        generate_autoprotocol_specialization(*read_protocol())

    if args.test_autoprotocol:
        print("Submitting Autoprotocol Test Run ...")
        proceed = input("Proceed? y/[n]")
        # proceed = "y"
        if proceed and proceed == "y":
            test_autoprotocol()

    if args.generate_emeraldcloud:
        print("Generating EmeraldCloud ...")
        generate_emeraldcloud_specialization(*read_protocol())
