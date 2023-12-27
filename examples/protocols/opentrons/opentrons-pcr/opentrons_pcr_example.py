import csv
import os

import sbol3
import tyto

import labop
from labop_convert.opentrons.opentrons_specialization import OT2Specialization

# Dev Note: This is a test of the initial version of the OT2 specialization. Any specs shown here can be changed in the future. Use at your own risk. Here be dragons.


def sanitize_display_id(display_id) -> str:
    invalid_chars = {c for c in display_id if not c.isalnum() and c != "_"}
    for c in invalid_chars:
        display_id = display_id.replace(c, "_")
    return display_id


def load_primer_layout(fname: str, doc: sbol3.Document):
    """Load layout of primer plate into a SampleArray"""
    contents = {}
    with open(fname, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            primer = row["Primer"]
            coordinate = row["Coordinates"]
            primer = sbol3.Component(
                sanitize_display_id(primer),
                name=primer,
                types=sbol3.SBO_DNA,
                roles=[tyto.SO.primer],
            )
            doc.add(primer)
            contents[coordinate] = primer.identity
    sample_array = labop.SampleArray()
    sample_array.format = "json"
    sample_array.from_dict(contents)
    return sample_array


def load_templates(fname: str, doc: sbol3.Document):
    """Load templates into a SampleArray"""
    with open(fname, "r") as f:
        reader = csv.DictReader(f)
        templates = set()
        for row in reader:
            template = row["Template"]
            templates.add(template)
    if len(templates) > 8:
        raise ValueError(
            f"This protocol only supports up to 8 templates {len(templates)} provided."
        )

    # Make SBOL Components
    templates = [
        sbol3.Component(
            "Component/" + sanitize_display_id(template),
            name=template,
            types=sbol3.SBO_DNA,
            roles=[tyto.SO.plasmid],
        )
        for template in templates
    ]
    doc.add(templates)

    # Make SampleArray of Components
    sample_array = labop.SampleArray()
    sample_array.format = "json"
    contents = {}
    for i, x in enumerate(templates):
        contents[f"C{i+1}"] = x.identity  # Assume that templates will go in row C
    sample_array.from_dict(contents)
    return sample_array


def load_pcr_plan(fname: str, doc: sbol3.Document):
    """Load planned PCR reactions"""
    with open(fname, "r") as f:
        reader = csv.DictReader(f)
        plan = {}
        for row in reader:
            f_primer = row["Forward"]
            r_primer = row["Reverse"]
            template = row["Template"]
            coordinate = row["Coordinates"]
            plan[coordinate] = dict(row)
    return plan


def create_protocol(doc, activity: labop.Protocol) -> labop.Protocol:
    from labop.constants import PREFIX_MAP, ddh2o, ludox

    ############################3
    # load pcr setup
    primer_layout = load_primer_layout("primer_layout.csv", doc)
    templates = load_templates("pcr_plan.csv", doc)
    pcr_plan = load_pcr_plan("pcr_plan.csv", doc)

    doc.add(ddh2o)
    doc.add(ludox)

    p300 = sbol3.Agent("p300_single", name="P300 Single")
    doc.add(p300)

    # Configure OT2 and load it with labware
    load = activity.primitive_step(
        "ConfigureRobot",
        instrument=OT2Specialization.EQUIPMENT["p300_single"],
        mount="left",
    )
    load = activity.primitive_step(
        "ConfigureRobot",
        instrument=OT2Specialization.EQUIPMENT["thermocycler"],
        mount="7",
    )
    # load = protocol.primitive_step('ConfigureRobot', instrument=OT2Specialization.EQUIPMENT['thermocycler'], mount='10')
    spec_tiprack = labop.ContainerSpec(
        "tiprack",
        queryString="cont:Opentrons96TipRack300uL",
        prefixMap=PREFIX_MAP,
    )
    load = activity.primitive_step(
        "LoadRackOnInstrument", rack=spec_tiprack, coordinates="1"
    )

    # Set up rack for reagents
    reagent_rack = labop.ContainerSpec(
        "reagent_rack",
        name="Tube rack for reagents",
        queryString="cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap",
        prefixMap=PREFIX_MAP,
    )
    rack = activity.primitive_step("EmptyRack", specification=reagent_rack)
    load_rack = activity.primitive_step(
        "LoadRackOnInstrument", rack=reagent_rack, coordinates="2"
    )

    # Set up primers plate
    primer_plate = labop.ContainerSpec(
        "primer_plate",
        name="primers in 96-well plate",
        queryString="cont:Corning96WellPlate360uLFlat",
        prefixMap=PREFIX_MAP,
    )
    load = activity.primitive_step(
        "LoadRackOnInstrument", rack=primer_plate, coordinates="3"
    )
    primer_plate = activity.primitive_step("EmptyContainer", specification=primer_plate)

    # Set up DNA polymerase
    polymerase = labop.ContainerSpec(
        "polymerase",
        name="DNA Polymerase",
        queryString="cont:StockReagent",
        prefixMap=PREFIX_MAP,
    )
    load_reagents = activity.primitive_step(
        "LoadContainerInRack",
        slots=rack.output_pin("slots"),
        container=polymerase,
        coordinates="A1",
    )

    # Set up water
    load_water = activity.primitive_step(
        "LoadContainerInRack",
        slots=rack.output_pin("slots"),
        container=labop.ContainerSpec(
            "water",
            name="tube for water",
            queryString="cont:MicrofugeTube",
            prefixMap=PREFIX_MAP,
        ),
        coordinates="B1",
    )
    provision_water = activity.primitive_step(
        "Provision",
        resource=ddh2o,
        destination=load_water.output_pin("samples"),
        amount=sbol3.Measure(500, tyto.OM.microliter),
    )

    # Template DNA samples are assumed to be in microfuge tubes
    # which will be added to a tube rack
    template_layout = {}
    for coordinate, template in templates.to_dict().items():
        template = doc.find(template)
        template_container = labop.ContainerSpec(
            template.display_id + "_container",
            name="container of " + template.name,
            queryString="cont:MicrofugeTube",
            prefixMap=PREFIX_MAP,
        )
        load_template = activity.primitive_step(
            "LoadContainerInRack",
            slots=rack.output_pin("slots"),
            container=template_container,
            coordinates=coordinate,
        )
        template_layout[template.name] = load_template.output_pin("samples")

    # Set up PCR machine
    pcr_plate = labop.ContainerSpec(
        "pcr_plate",
        name="PCR plate",
        queryString="cont:Biorad96WellPCRPlate",
        prefixMap=PREFIX_MAP,
    )
    load_pcr_plate_on_thermocycler = activity.primitive_step(
        "LoadContainerOnInstrument",
        specification=pcr_plate,
        instrument=OT2Specialization.EQUIPMENT["thermocycler"],
        slots="A1:H12",
    )

    # Pipette PCR reactions
    for target_well, reaction in pcr_plan.items():
        f_primer = reaction["Forward"]
        [f_primer_coordinates] = [
            c
            for c, p in primer_layout.to_dict().items()
            if doc.find(p).name == f_primer
        ]
        r_primer = reaction["Reverse"]
        [r_primer_coordinates] = [
            c
            for c, p in primer_layout.to_dict().items()
            if doc.find(p).name == r_primer
        ]
        template = template_layout[reaction["Template"]]

        target_sample = activity.primitive_step(
            "PlateCoordinates",
            source=load_pcr_plate_on_thermocycler.output_pin("samples"),
            coordinates=target_well,
        )

        # Transfer water
        transfer = activity.primitive_step(
            "Transfer",
            source=load_water.output_pin("samples"),
            destination=target_sample.output_pin("samples"),
            amount=sbol3.Measure(6, tyto.OM.microliter),
        )
        transfer.name = "Add water"

        # Transfer forward primer
        f_primer_sample = activity.primitive_step(
            "PlateCoordinates",
            source=primer_plate.output_pin("samples"),
            coordinates=f_primer_coordinates,
        )
        transfer = activity.primitive_step(
            "Transfer",
            source=f_primer_sample.output_pin("samples"),
            destination=target_sample.output_pin("samples"),
            amount=sbol3.Measure(1, tyto.OM.microliter),
        )
        transfer.name = "Add F primer"

        # Transfer reverse primer
        r_primer_sample = activity.primitive_step(
            "PlateCoordinates",
            source=primer_plate.output_pin("samples"),
            coordinates=r_primer_coordinates,
        )
        transfer = activity.primitive_step(
            "Transfer",
            source=r_primer_sample.output_pin("samples"),
            destination=target_sample.output_pin("samples"),
            amount=sbol3.Measure(1, tyto.OM.microliter),
        )
        transfer.name = "Add R primer"

        # Transfer template
        transfer = activity.primitive_step(
            "Transfer",
            source=template,
            destination=target_sample.output_pin("samples"),
            amount=sbol3.Measure(1, tyto.OM.microliter),
        )
        transfer.name = "Add template"

        # Transfer polymerase
        transfer = activity.primitive_step(
            "Transfer",
            source=load_reagents.output_pin("samples"),
            destination=target_sample.output_pin("samples"),
            amount=sbol3.Measure(1, tyto.OM.microliter),
        )
        transfer.name = "Add polymerase"

    pcr = activity.primitive_step(
        "PCR",
        denaturation_temp=sbol3.Measure(98.0, tyto.OM.degree_Celsius),
        denaturation_time=sbol3.Measure(10, tyto.OM.second),
        annealing_temp=sbol3.Measure(45.0, tyto.OM.degree_Celsius),
        annealing_time=sbol3.Measure(5, tyto.OM.second),
        extension_temp=sbol3.Measure(65.0, tyto.OM.degree_Celsius),
        extension_time=sbol3.Measure(60, tyto.OM.second),
        cycles=30,
    )

    return activity


if __name__ == "__main__":
    harness = labop.execution.harness.ProtocolHarness(
        base_dir=os.path.dirname(__file__),
        entry_point=create_protocol,
        artifacts=[
            labop.execution.harness.ProtocolSpecialization(
                specialization=OT2Specialization("ot2_pcr_labop")
            )
        ],
        libraries=[
            "liquid_handling",
            "plate_handling",
            "spectrophotometry",
            "sample_arrays",
            "pcr",
        ],
        namespace="https://bbn.com/scratch/",
        protocol_name="pcr_example",
        protocol_long_name="Opentrons PCR Demo",
        protocol_version="1.0",
        agent="ot2_machine",
        execution_flags={"failsafe": False},
        execution_id="test_execution",
    )
    harness.run(verbose=True)
