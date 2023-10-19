import sbol3
import tyto

import labop
from labop.constants import PREFIX_MAP, ddh2o, ludox
from labop.execution.harness import ProtocolHarness, ProtocolSpecialization
from labop.protocol import Protocol
from labop.strings import Strings
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization
from labop_convert.opentrons.opentrons_specialization import OT2Specialization

# Dev Note: This is a test of the initial version of the OT2 specialization. Any specs shown here can be changed in the future. Use at your own risk. Here be dragons.


def generate_protocol(doc: sbol3.Document, activity: Protocol) -> Protocol:
    # create the materials to be provisioned

    doc.add(ddh2o)
    doc.add(ludox)

    p300 = sbol3.Agent("p300_single", name="P300 Single")
    doc.add(p300)
    load = activity.primitive_step("ConfigureInstrument", instrument=p300, mount="left")

    # Define labware
    spec_rack = labop.ContainerSpec(
        "working_reagents_rack",
        name="rack for reagent aliquots",
        queryString="cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap",
        prefixMap=PREFIX_MAP,
    )
    spec_ludox_container = labop.ContainerSpec(
        "ludox_working_solution",
        name="tube for ludox working solution",
        queryString="cont:MicrofugeTube",
        prefixMap=PREFIX_MAP,
    )
    spec_water_container = labop.ContainerSpec(
        "water_stock",
        name="tube for water aliquot",
        queryString="cont:MicrofugeTube",
        prefixMap=PREFIX_MAP,
    )
    spec_plate = labop.ContainerSpec(
        "calibration_plate",
        name="calibration plate",
        queryString="cont:Corning96WellPlate360uLFlat",
        prefixMap=PREFIX_MAP,
    )
    spec_tiprack = labop.ContainerSpec(
        "tiprack",
        queryString="cont:Opentrons96TipRack300uL",
        prefixMap=PREFIX_MAP,
    )
    doc.add(spec_rack)
    doc.add(spec_ludox_container)
    doc.add(spec_water_container)
    doc.add(spec_plate)
    doc.add(spec_tiprack)

    # Load OT2 instrument with labware
    load = activity.primitive_step(
        "LoadRackOnInstrument", rack=spec_rack, coordinates="1"
    )
    load = activity.primitive_step(
        "LoadRackOnInstrument", rack=spec_tiprack, coordinates="2"
    )
    load = activity.primitive_step(
        "LoadRackOnInstrument", rack=spec_plate, coordinates="3"
    )

    # Set up reagents
    rack = activity.primitive_step("EmptyRack", specification=spec_rack)
    load_rack1 = activity.primitive_step(
        "LoadContainerInRack",
        slots=rack.output_pin("slots"),
        container=spec_ludox_container,
        coordinates="A1",
    )
    load_rack2 = activity.primitive_step(
        "LoadContainerInRack",
        slots=rack.output_pin("slots"),
        container=spec_water_container,
        coordinates="A2",
    )
    provision = activity.primitive_step(
        "Provision",
        resource=ludox,
        destination=load_rack1.output_pin("samples"),
        amount=sbol3.Measure(500, tyto.OM.microliter),
    )
    provision = activity.primitive_step(
        "Provision",
        resource=ddh2o,
        destination=load_rack2.output_pin("samples"),
        amount=sbol3.Measure(500, tyto.OM.microliter),
    )

    # Set up target samples
    plate = activity.primitive_step("EmptyContainer", specification=spec_plate)
    water_samples = activity.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A1:D1",
    )
    ludox_samples = activity.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A2:D2",
    )

    transfer = activity.primitive_step(
        "Transfer",
        source=load_rack1.output_pin("samples"),
        destination=water_samples.output_pin("samples"),
        amount=sbol3.Measure(100, tyto.OM.microliter),
    )
    transfer = activity.primitive_step(
        "Transfer",
        source=load_rack1.output_pin("samples"),
        destination=ludox_samples.output_pin("samples"),
        amount=sbol3.Measure(100, tyto.OM.microliter),
    )

    return activity


if __name__ == "__main__":
    harness = ProtocolHarness(
        entry_point=generate_protocol,
        artifacts=[
            ProtocolSpecialization(
                specialization=MarkdownSpecialization(
                    "opentrons_ludox_example_protocol.md",
                    sample_format=Strings.XARRAY,
                )
            ),
            ProtocolSpecialization(
                specialization=OT2Specialization("opentrons_ludox_example_labop.py")
            ),
        ],
        namespace="https://labop.io/examples/protocols/opentrons/",
        protocol_name="iGEM_LUDOX_OD_calibration_2018",
        protocol_long_name="iGEM 2018 LUDOX OD calibration protocol for OT2",
        protocol_version="1.0",
        protocol_description="Test Execution",
        agent=sbol3.Agent("ot2_machine", name="OT2 machine"),
    )
    harness.run()
