import json
import logging
import os
from typing import Tuple

import rdflib as rdfl
import sbol3
import tyto
from sbol3 import Document

import labop
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import (
    MarkdownSpecialization,
)

logger: logging.Logger = logging.Logger("LUDOX_protocol")

CONT_NS = rdfl.Namespace("https://sift.net/container-ontology/container-ontology#")
OM_NS = rdfl.Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")


def prepare_document() -> Document:
    logger.info("Setting up document")
    doc = sbol3.Document()
    sbol3.set_namespace("https://bbn.com/scratch/")
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


DOCSTRING = """
With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
        """


def create_protocol() -> labop.Protocol:
    logger.info("Creating protocol")
    protocol: labop.Protocol = labop.Protocol("iGEM_LUDOX_OD_calibration_2018")
    protocol.name = "iGEM 2018 LUDOX OD calibration protocol"
    protocol.description = DOCSTRING
    return protocol


def create_h2o() -> sbol3.Component:
    ddh2o = sbol3.Component(
        "ddH2O", "https://identifiers.org/pubchem.substance:24901740"
    )
    ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"  # TODO get via tyto
    return ddh2o


def create_ludox() -> sbol3.Component:
    ludox = sbol3.Component(
        "LUDOX", "https://identifiers.org/pubchem.substance:24866361"
    )
    ludox.name = "LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O"
    return ludox


PLATE_SPECIFICATION = """cont:ClearPlate and
 cont:SLAS-4-2004 and
 (cont:wellVolume some
    ((om:hasUnit value om:microlitre) and
     (om:hasNumericalValue only xsd:decimal[>= "200"^^xsd:decimal])))"""
PLATE_SPECIFICATION = "cont:Plate96Well"
PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


def create_plate(protocol: labop.Protocol):
    spec = labop.ContainerSpec(
        "plateRequirement",
        name="calibration plate",
        queryString=PLATE_SPECIFICATION,
        prefixMap=PREFIX_MAP,
    )
    plate = protocol.primitive_step("EmptyContainer", specification=spec)
    plate.name = "calibration plate"
    return plate


def provision_h2o(protocol: labop.Protocol, plate, ddh2o) -> None:
    c_ddh2o = protocol.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A1:D1",
    )
    protocol.primitive_step(
        "Provision",
        resource=ddh2o,
        destination=c_ddh2o.output_pin("samples"),
        amount=sbol3.Measure(100, tyto.OM.microliter),
    )


def provision_ludox(protocol: labop.Protocol, plate, ludox) -> None:
    c_ludox = protocol.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A2:D2",
    )
    protocol.primitive_step(
        "Provision",
        resource=ludox,
        destination=c_ludox.output_pin("samples"),
        amount=sbol3.Measure(100, tyto.OM.microliter),
    )


def measure_absorbance(protocol: labop.Protocol, plate, wavelength_param):
    c_measure = protocol.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A1:D2",
    )
    return protocol.primitive_step(
        "MeasureAbsorbance",
        samples=c_measure.output_pin("samples"),
        wavelength=wavelength_param,
    )


def measure_fluorescence(
    protocol: labop.Protocol, plate, excitation, emission, bandpass
):
    c_measure = protocol.primitive_step(
        "PlateCoordinates",
        source=plate.output_pin("samples"),
        coordinates="A1:D2",
    )
    return protocol.primitive_step(
        "MeasureFluorescence",
        samples=c_measure.output_pin("samples"),
        excitationWavelength=sbol3.Measure(excitation, tyto.OM.nanometer),
        emissionWavelength=sbol3.Measure(emission, tyto.OM.nanometer),
        emissionBandpassWidth=sbol3.Measure(bandpass, tyto.OM.nanometer),
        gain=5000,
    )


def ludox_protocol() -> Tuple[labop.Protocol, Document]:
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

    # create the materials to be provisioned
    ddh2o = create_h2o()
    doc.add(ddh2o)

    ludox = create_ludox()
    doc.add(ludox)

    # add an optional parameter for specifying the wavelength
    wavelength_param = protocol.input_value(
        "wavelength",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(600, tyto.OM.nanometer),
    )

    # actual steps of the protocol
    # get a plate
    plate = create_plate(protocol)

    # put ludox and water in selected wells
    provision_h2o(protocol, plate, ddh2o)
    provision_ludox(protocol, plate, ludox)

    # measure the absorbance
    measure = measure_absorbance(protocol, plate, wavelength_param)

    output = protocol.designate_output(
        "absorbance", sbol3.OM_MEASURE, measure.output_pin("measurements")
    )

    protocol.order(protocol.get_last_step(), output)

    protocol.order(protocol.get_last_step(), protocol.final())

    return protocol, doc


if __name__ == "__main__":
    new_protocol: labop.Protocol
    new_protocol, doc = ludox_protocol()
    print("Validating and writing protocol")
    v = doc.validate()
    assert len(v) == 0, "".join(f"\n {e}" for e in v)

    rdf_filename = os.path.join(
        os.path.dirname(__file__), "iGEM 2018 LUDOX OD calibration protocol.nt"
    )
    doc.write(rdf_filename, sbol3.SORTED_NTRIPLES)
    print(f"Wrote file as {rdf_filename}")

    # render and view the dot
    dot = new_protocol.to_dot()
    dot.render(f"{new_protocol.name}.gv")
    dot.view()

    agent = sbol3.Agent("test_agent")
    ee = ExecutionEngine(
        specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")]
    )
    x = ee.execute(new_protocol, agent, id="test_execution", parameter_values=[])
