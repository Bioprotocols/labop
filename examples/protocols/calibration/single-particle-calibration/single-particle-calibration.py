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

NAMESPACE = "http://igem.org/engineering/"
PROTOCOL_NAME = "interlab"
PROTOCOL_LONG_NAME = "Fluorescence per bacterial particle calibration"

if "unittest" in sys.modules:
    REGENERATE_ARTIFACTS = False
else:
    REGENERATE_ARTIFACTS = True

OUT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

filename = "".join(__file__.split(".py")[0].split("/")[-1:])


def generate_resuspend_subprotocol(doc: sbol3.Document):
    import labop

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
        samples=destination,
        duration=sbol3.Measure(30, OM.second),
    )
    subprotocol.order(vortex, subprotocol.final())
    return subprotocol


def generate_solution_subprotocol(doc: sbol3.Document):
    import labop

    subprotocol = labop.Protocol("PrepareSolution")
    doc.add(subprotocol)

    resuspend_subprotocol = generate_resuspend_subprotocol(doc)

    container_spec_param = subprotocol.input_value("specification", labop.ContainerSpec)

    reagent_param = subprotocol.input_value("reagent", sbol3.Component)
    reagent_mass_param = subprotocol.input_value("reagent_mass", sbol3.Measure)
    buffer_param = subprotocol.input_value("buffer", sbol3.Component)
    buffer_volume = subprotocol.input_value("buffer_volume", sbol3.Measure)
    buffer_container = subprotocol.input_value("buffer_container", labop.SampleArray)
    # target_concentration = subprotocol.input_value(
    #     "target_concentration", sbol3.Measure
    # )

    # solution_name = f"calibrant"
    # Provision an empty Microfuge tube in which to mix the standard solution
    standard_solution_container = subprotocol.primitive_step(
        "EmptyContainer", specification=container_spec_param
    )
    # standard_solution_container.name = solution_name

    provision = subprotocol.primitive_step(
        "Provision",
        resource=reagent_param,
        destination=standard_solution_container.output_pin("samples"),
        amount=reagent_mass_param,
    )
    ### Suspend calibrant dry reagents
    suspend_reagent = subprotocol.primitive_step(
        resuspend_subprotocol,
        source=buffer_container,
        destination=standard_solution_container.output_pin("samples"),
        amount=buffer_volume,
    )
    # suspend_reagent.description = f"The reconstituted `{reagent.name}` should have a final concentration of {target_concentration} in `{buffer.name}`."

    subprotocol.designate_output(
        "samples",
        "http://bioprotocols.org/labop#SampleArray",
        source=standard_solution_container.output_pin("samples"),
    )
    subprotocol.order(suspend_reagent, subprotocol.final())
    return subprotocol


def generate_prepare_reagents_subprotocol(doc: sbol3.Document):
    import labop

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
    silica_beads.description = "3e9 NanoCym microspheres"  # where does this go?

    doc.add(ddh2o)
    doc.add(silica_beads)

    subprotocol = labop.Protocol("PrepareReagents")
    doc.add(subprotocol)

    solution_subprotocol = generate_solution_subprotocol(doc)

    ddh2o_container = subprotocol.primitive_step(
        "EmptyContainer",
        specification=labop.ContainerSpec(
            "ddh2o_container",
            name="molecular grade H2O",
            queryString="cont:StockReagent50mL",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
    )
    ddh2o_container.name = "ddh2o_container"

    provision = subprotocol.primitive_step(
        "Provision",
        resource=ddh2o,
        destination=ddh2o_container.output_pin("samples"),
        amount=sbol3.Measure(12, OM.milliliter),
    )

    output1 = subprotocol.designate_output(
        "ddh2o_container",
        "http://bioprotocols.org/labop#SampleArray",
        source=ddh2o_container.output_pin("samples"),
    )

    silica_beads_solution_subprotocol = subprotocol.primitive_step(
        solution_subprotocol,
        specification=labop.ContainerSpec(
            "microspheres",
            name="microspheres",
            queryString="cont:StockReagent",
            prefixMap={
                "cont": "https://sift.net/container-ontology/container-ontology#"
            },
        ),
        reagent=silica_beads,
        reagent_mass=sbol3.Measure(2, OM.gram),
        buffer=ddh2o,
        buffer_volume=sbol3.Measure(1, OM.millilitre),
        buffer_container=ddh2o_container.output_pin("samples"),
        # target_concentration=sbol3.Measure(10, OM.micromolar)
    )
    silica_beads_solution_subprotocol.name = "microsphere_standard_solution_container"
    output4 = subprotocol.designate_output(
        "microsphere_standard_solution_container",
        "http://bioprotocols.org/labop#SampleArray",
        source=silica_beads_solution_subprotocol.output_pin("samples"),
    )

    subprotocol.order(silica_beads_solution_subprotocol, subprotocol.final())
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

    protocol = labop.Protocol(PROTOCOL_NAME)
    protocol.name = PROTOCOL_LONG_NAME
    protocol.version = "1.2"
    protocol.description = """
Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56).
    This protocol corresponds to ECL protocol "id:M8n3rxnBlZMM".
    """
    doc.add(protocol)

    prepare_reagents_subprotocol = generate_prepare_reagents_subprotocol(doc)

    prepare_reagents = protocol.primitive_step(prepare_reagents_subprotocol)
    prepare_reagents.name = "prepare_reagents"

    ddh2o_container = prepare_reagents.output_pin("ddh2o_container")

    microsphere_standard_solution_container = prepare_reagents.output_pin(
        "microsphere_standard_solution_container"
    )

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

    silica_beads_wells_A1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1",
    )

    # Plate blanks
    blank_wells1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="B1:H1,A2:C2",
    )

    # Plate blanks
    water_wells1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="D2",
    )

    transfer_blanks1 = protocol.primitive_step(
        "Transfer",
        source=ddh2o_container,
        destination=blank_wells1.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )

    ### Plate calibrants in first column
    transfer1 = protocol.primitive_step(
        "Transfer",
        source=microsphere_standard_solution_container,
        destination=silica_beads_wells_A1.output_pin("samples"),
        amount=sbol3.Measure(200, OM.microlitre),
    )
    transfer2 = protocol.primitive_step(
        "Transfer",
        source=microsphere_standard_solution_container,
        destination=water_wells1.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
    )

    dilution_series1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1:H1,A2:C2",
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
        direction=labop.Strings.COLUMN_DIRECTION,
        diluent=doc.find("ddH2O"),
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

    discard_wells = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="C2",
    )

    discard = protocol.primitive_step(
        "Transfer",
        source=discard_wells.output_pin("samples"),
        amount=sbol3.Measure(100, OM.microlitre),
        destination=discard_container.output_pin("samples"),
    )

    discard.description = " This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination."

    # Perform measurements
    read_wells1 = protocol.primitive_step(
        "PlateCoordinates",
        source=calibration_plate.output_pin("samples"),
        coordinates="A1:H1,A2:D2",
    )

    measure_absorbance = protocol.primitive_step(
        "MeasureAbsorbance",
        samples=read_wells1.output_pin("samples"),
        wavelength=sbol3.Measure(600, OM.nanometer),
    )

    compute_metadata = protocol.primitive_step(
        "ComputeMetadata", for_samples=calibration_plate.output_pin("samples")
    )

    meta1 = protocol.primitive_step(
        "JoinMetadata",
        dataset=measure_absorbance.output_pin("measurements"),
        metadata=compute_metadata.output_pin("metadata"),
    )

    outnode = protocol.designate_output(
        "dataset",
        "http://bioprotocols.org/labop#Dataset",
        source=meta1.output_pin("enhanced_dataset"),
    )

    protocol.order(outnode, protocol.final())

    if REGENERATE_ARTIFACTS:
        protocol.to_dot().render(os.path.join(OUT_DIR, filename))
        protocol_file = os.path.join(OUT_DIR, f"{filename}-protocol.nt")
        with open(protocol_file, "w") as f:
            print(f"Saving protocol [{protocol_file}].")
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())

    return protocol, doc


def compute_sample_trajectory(protocol, doc):
    import labop
    from labop.execution.execution_engine import ExecutionEngine
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
    from labop.execution.execution_engine import ExecutionEngine
    from labop.strings import Strings
    from labop_convert import MarkdownSpecialization

    if REGENERATE_ARTIFACTS:
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
    from labop.execution.execution_engine import ExecutionEngine
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
    from labop.execution.execution_engine import ExecutionEngine
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

    ee = ExecutionEngine(
        specializations=[autoprotocol_specialization],
        out_dir=OUT_DIR,
        failsafe=False,
    )
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


def generate_emeraldcloud_specialization(protocol, doc, stock_solutions=None):
    blockPrint()
    import labop
    import uml
    from labop.execution.execution_engine import ExecutionEngine
    from labop_convert.emeraldcloud.ecl_specialization import ECLSpecialization

    ddh2o = doc.find(f"{NAMESPACE}ddH2O")
    pbs = doc.find(f"{NAMESPACE}pbs")
    fluorescein = doc.find(f"{NAMESPACE}fluorescein")
    silica_beads = doc.find(f"{NAMESPACE}silica_beads")
    discard_container = [x for x in protocol.nodes if x.name == "discard_container"][0]
    fluorescein_standard_solution_container = [
        x
        for p in doc.objects
        if isinstance(p, labop.Protocol)
        for x in p.nodes
        if isinstance(x, uml.CallBehaviorAction) and x.name == "fluroscein_calibrant"
    ][0]
    microsphere_standard_solution_container = [
        x
        for p in doc.objects
        if isinstance(p, labop.Protocol)
        for x in p.nodes
        if isinstance(x, uml.CallBehaviorAction)
        and x.name == "microsphere_standard_solution_container"
    ][0]
    # ddh2o_container = [x for x in protocol.nodes if x.name == "ddh2o_container"][0]
    # pbs_container = [x for x in protocol.nodes if x.name == "pbs_container"][0]
    calibration_plate = [x for x in protocol.nodes if x.name == "calibration_plate"][0]

    if stock_solutions:
        microsphere_reagent_id = stock_solutions["microspheres"]
        fluorescein_regagent_id = stock_solutions["fluorescein"]
    else:
        microsphere_reagent_id = (
            """Model[Sample, "Silica Nanoparticle 950nm Nanocym"]"""
        )
        fluorescein_regagent_id = """Model[Sample, "Fluorescein, sodium salt"]"""

    resolutions = {
        ddh2o.identity: """Model[Sample, "Nuclease-free Water"]""",
        pbs.identity: """Model[Sample, StockSolution, "1x PBS from 10X stock"]""",
        fluorescein.identity: f"""{fluorescein_regagent_id}""",
        silica_beads.identity: f"""{microsphere_reagent_id}""",
        discard_container.input_pin("specification")
        .value.value.lookup()
        .identity: """Model[Container, Vessel, "2mL Tube"]""",
        fluorescein_standard_solution_container.input_pin("specification")
        .value.value.lookup()
        .identity: '"Fluorescein calibrant"',
        microsphere_standard_solution_container.input_pin("specification")
        .value.value.lookup()
        .identity: f'"microspheres"',
        # ddh2o_container.input_pin("specification")
        # .value.value.lookup()
        # .identity: "Nuclease-free Water",
        # pbs_container.input_pin("specification")
        # .value.value.lookup()
        # .identity: "1x PBS from 10X stock",
        calibration_plate.input_pin("specification")
        .value.value.lookup()
        .identity: """Model[Container, Plate, "96-well Polystyrene Flat-Bottom Plate, Clear"]""",
    }

    if stock_solutions:
        ecl_output = os.path.join(OUT_DIR, f"{filename}-emeraldcloud.nb")
    else:
        ecl_output = os.path.join(
            OUT_DIR, f"{filename}-emeraldcloud-stock-solutions.nb"
        )
    ecl_specialization = ECLSpecialization(
        ecl_output,
        resolutions=resolutions,
        create_stock_solutions=(stock_solutions is None),
    )

    ee = ExecutionEngine(
        specializations=[ecl_specialization], out_dir=OUT_DIR, failsafe=False
    )
    execution = ee.execute(
        protocol,
        sbol3.Agent("test_agent"),
        id="test_execution",
        parameter_values=[],
    )

    enablePrint()

    print(f"Saving EmeraldCloud [{ecl_output}].")

    if REGENERATE_ARTIFACTS:
        execution_filename = os.path.join(OUT_DIR, f"{filename}-execution.nt")
        print(f"Saving Execution Record [{execution_filename}]")
        with open(execution_filename, "w") as f:
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
        "-s",
        "--generate-emeraldcloud-stock-solutions",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the Emerald Cloud notebook at artifacts/{filename}-emeraldcloud.nb.",
    )
    parser.add_argument(
        "-e",
        "--generate-emeraldcloud",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the Emerald Cloud notebook at artifacts/{filename}-emeraldcloud.nb. ",
    )
    parser.add_argument(
        "--ecl-microsphere-id",
        nargs="?",
        const='Model[Sample, StockSolution, "id:L8kPEjk1vmRP"]',
        default='Model[Sample, StockSolution, "id:L8kPEjk1vmRP"]',
        type=str,
        help=f"Execute the protocol to generate the Emerald Cloud notebook at artifacts/{filename}-emeraldcloud.nb. Optionally specify an id for the microsphere reagent.  Only valid in conjunction with the -e flag.",
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

    if args.generate_emeraldcloud_stock_solutions:
        print("Generating EmeraldCloud Stock Solution Recipes ...")
        generate_emeraldcloud_specialization(*read_protocol())

    if args.generate_emeraldcloud:
        print("Generating EmeraldCloud ...")
        generate_emeraldcloud_specialization(
            *read_protocol(),
            stock_solutions={
                "microspheres": f"{args.ecl_microsphere_id}",
                "fluorescein": """Model[Sample, StockSolution, "1x PBS, 10uM Fluorescein"]""",
            },
        )
