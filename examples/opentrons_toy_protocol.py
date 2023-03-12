from logging import Logger
import os
import logging
import sbol3
import labop
import tyto
import uml
import json
import rdflib as rdfl
from typing import Dict, Tuple
from sbol3 import Document

from labop.execution_engine import ExecutionEngine
from labop_convert.opentrons.opentrons_specialization import (
    OT2Specialization,
    REVERSE_LABWARE_MAP,
)

logger: logging.Logger = logging.Logger("OT2_demo")

CONT_NS = rdfl.Namespace("https://sift.net/container-ontology/container-ontology#")
OM_NS = rdfl.Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")
PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


def prepare_document() -> Document:
    logger.info("Setting up document")
    doc = sbol3.Document()
    sbol3.set_namespace("https://labop.io/scratch/")
    return doc


def import_labop_libraries() -> None:
    logger.info("Importing libraries")
    labop.import_library("liquid_handling")
    logger.info("... Imported liquid handling")
    labop.import_library("plate_handling")
    logger.info("... Imported plate handling")
    labop.import_library("spectrophotometry")
    logger.info("... Imported spectrophotometry")
    labop.import_library("sample_arrays")
    logger.info("... Imported sample arrays")


def create_protocol() -> labop.Protocol:
    logger.info("Creating protocol")
    protocol: labop.Protocol = labop.Protocol("OT2_demo")
    protocol.name = "OT2 demo"
    protocol.description = "Example Opentrons Protocol as LabOP"
    return protocol


def get_container(protocol: labop.Protocol, container_name: str, container_type: str):
    query_string = REVERSE_LABWARE_MAP[container_type]
    plate_spec = labop.ContainerSpec(
        container_name.replace(" ", "_"),
        name=container_name,
        queryString=query_string,
        prefixMap=PREFIX_MAP,
    )
    plate = protocol.primitive_step("EmptyContainer", specification=plate_spec)
    return plate


def get_samples_from_coordinates(protocol, container, coordinates):
    return protocol.primitive_step(
        "PlateCoordinates", source=container, coordinates=coordinates
    ).output_pin("samples")


def opentrons_toy_protocol() -> Tuple[labop.Protocol, Document]:
    #############################################
    # set up the document
    doc: Document = prepare_document()

    #############################################
    # Import the primitive libraries
    import_labop_libraries()

    #############################################
    # Create the protocol
    protocol: labop.Protocol = create_protocol()
    doc.add(protocol)

    # plate = protocol.load_labware('corning_96_wellplate_360ul_flat', location='1')
    create_plate = get_container(
        protocol, "sample plate", "corning_96_wellplate_360ul_flat"
    )
    load_plate = protocol.primitive_step(
        "LoadRackOnInstrument",
        rack=create_plate.input_pin("specification").value.get_value(),
        coordinates="1",
    )

    # tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', location='2')
    create_tiprack = get_container(protocol, "tiprack", "opentrons_96_tiprack_300ul")
    tiprack = protocol.primitive_step(
        "LoadRackOnInstrument",
        rack=create_tiprack.input_pin("specification").value.get_value(),
        coordinates="2",
    )

    # left_pipette = protocol.load_instrument(
    #          'p300_single', mount='left', tip_racks=[tiprack])
    p300 = sbol3.Agent("p300_single", name="P300 Single")
    doc.add(p300)
    left_pipette = protocol.primitive_step(
        "ConfigureRobot", instrument=p300, mount="left"
    )

    # left_pipette.pick_up_tip()
    # left_pipette.aspirate(100, plate['A1'])
    # left_pipette.dispense(100, plate['B2'])
    # left_pipette.drop_tip()
    # source_well = protocol.primitive_step(
    #     "PlateCoordinates", source=create_plate.output_pin("samples"), coordinates="A1"
    # )
    # dest_well = protocol.primitive_step(
    #     "PlateCoordinates", source=create_plate.output_pin("samples"), coordinates="B2"
    # )
    transfer = protocol.primitive_step(
        "Transfer",
        source=get_samples_from_coordinates(
            protocol, create_plate.output_pin("samples"), "A1"
        ),
        destination=get_samples_from_coordinates(
            protocol, create_plate.output_pin("samples"), "B2"
        ),
        amount=sbol3.Measure(100, tyto.OM.microliter),
    )

    protocol.order(transfer, protocol.final())

    return protocol, doc
