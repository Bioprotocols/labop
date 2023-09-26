import logging

import sbol3
import tyto
from sbol3 import Document

import labop
from labop.constants import ddh2o, ludox
from labop.strings import Strings
from labop.utils.harness import ProtocolHarness, ProtocolSpecialization
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization

logger: logging.Logger = logging.Logger(__name__)


PLATE_SPECIFICATION = """cont:ClearPlate and
 cont:SLAS-4-2004 and
 (cont:wellVolume some
    ((om:hasUnit value om:microlitre) and
     (om:hasNumericalValue only xsd:decimal[>= "200"^^xsd:decimal])))"""


def create_plate(protocol: labop.Protocol):
    spec = labop.ContainerSpec(
        "plateRequirement",
        name="calibration plate",
        queryString=PLATE_SPECIFICATION,
        prefixMap=labop.constants.PREFIX_MAP,
    )
    plate = protocol.primitive_step("EmptyContainer", specification=spec)
    plate.name = "calibration plate"
    return plate


def provision_h2o(protocol: labop.Protocol, plate) -> None:
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


def provision_ludox(protocol: labop.Protocol, plate) -> None:
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


def ludox_protocol(doc: Document, protocol: labop.Protocol) -> labop.Protocol:
    # create the materials to be provisioned
    doc.add(ddh2o)
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
    provision_h2o(protocol, plate)
    provision_ludox(protocol, plate)

    # measure the absorbance
    measure = measure_absorbance(protocol, plate, wavelength_param)

    output = protocol.designate_output(
        "absorbance", sbol3.OM_MEASURE, measure.output_pin("measurements")
    )

    protocol.order(protocol.get_last_step(), output)

    protocol.order(protocol.get_last_step(), protocol.final())

    return protocol


harness = ProtocolHarness(
    entry_point=ludox_protocol,
    artifacts=[
        ProtocolSpecialization(
            specialization=MarkdownSpecialization(
                "test_LUDOX_markdown.md",
                sample_format=Strings.XARRAY,
            )
        )
    ],
    namespace="https://labop.io/examples/protocols/ludox/",
    protocol_name="iGEM_LUDOX_OD_calibration_2018",
    protocol_long_name="iGEM 2018 LUDOX OD calibration protocol",
    protocol_version="1.0",
    protocol_description="""
With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
        """,
)

if __name__ == "__main__":
    harness.run()
