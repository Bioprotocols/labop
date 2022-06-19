import json
import logging
import os
from typing import Tuple

import rdflib as rdfl
import sbol3
import tyto
from sbol3 import Document

import paml
import uml

logger: logging.Logger = logging.Logger("pH_calibration")

CONT_NS = rdfl.Namespace(
    "https://sift.net/container-ontology/container-ontology#"
)
OM_NS = rdfl.Namespace(
    "http://www.ontology-of-units-of-measure.org/resource/om-2/"
)


def prepare_document() -> Document:
    logger.info("Setting up document")
    doc = sbol3.Document()
    sbol3.set_namespace("https://bbn.com/scratch/")
    return doc


def import_paml_libraries() -> None:
    logger.info("Importing libraries")
    paml.import_library("liquid_handling")
    logger.info("... Imported liquid handling")
    paml.import_library("plate_handling")
    logger.info("... Imported plate handling")
    paml.import_library("spectrophotometry")
    logger.info("... Imported spectrophotometry")
    paml.import_library("sample_arrays")
    logger.info("... Imported sample arrays")


DOCSTRING = (
    "This protocol implements a pH calibration protocol with decision nodes."
)


def create_protocol() -> paml.Protocol:
    logger.info("Creating protocol")
    protocol: paml.Protocol = paml.Protocol("pH_calibration_protocol")
    protocol.name = "pH calibration protocol"
    protocol.description = DOCSTRING
    return protocol


def create_subprotocol(doc) -> paml.Protocol:
    logger.info("Creating subprotocol")
    protocol: paml.Protocol = paml.Protocol("pH_adjustment_protocol")
    protocol.name = "pH adjustment protocol"
    protocol.description = "pH adjustment protocol"
    doc.add(protocol)

    reaction_vessel = protocol.input_value(
        "reaction_vessel",
        paml.SampleArray,
    )

    naoh_container = protocol.input_value(
        "naoh_container",
        paml.SampleArray,
    )

    protocol.execute_primitive(
        "Transfer",
        source=naoh_container,
        destination=reaction_vessel,
        amount=sbol3.Measure(100, tyto.OM.milligram),
    )

    return protocol


# def create_h2o() -> sbol3.Component:
#     ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
#     ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # TODO get via tyto
#     return ddh2o


# def create_ludox() -> sbol3.Component:
#     ludox = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
#     ludox.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
#     return ludox


# PLATE_SPECIFICATION = \
#     """cont:ClearPlate and
#  cont:SLAS-4-2004 and
#  (cont:wellVolume some
#     ((om:hasUnit value om:microlitre) and
#      (om:hasNumericalValue only xsd:decimal[>= "200"^^xsd:decimal])))"""

# PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


# def create_plate(protocol: paml.Protocol):
#     # graph: rdfl.Graph = protocol._other_rdf
#     # plate_spec_uri = \
#     #     "https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018/container_requirement#RequiredPlate"
#     # graph.add((plate_spec_uri, CONT_NS.containerOntologyQuery, PLATE_SPECIFICATION))
#     # plate_spec = sbol3.Identified(plate_spec_uri,
#     #                               "foo", name="RequiredPlate")
#     spec = paml.ContainerSpec(queryString=PLATE_SPECIFICATION, prefixMap=PREFIX_MAP, name='plateRequirement')
#     plate = protocol.primitive_step('EmptyContainer',
#                                     specification=spec)
#     plate.name = 'calibration plate'
#     return plate


# def provision_h2o(protocol: paml.Protocol, plate, ddh2o) -> None:
#     c_ddh2o = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:D1')
#     protocol.primitive_step('Provision', resource=ddh2o, destination=c_ddh2o.output_pin('samples'),
#                             amount=sbol3.Measure(100, tyto.OM.microliter))


# def provision_ludox(protocol: paml.Protocol, plate, ludox) -> None:
#     c_ludox = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A2:D2')
#     protocol.primitive_step('Provision', resource=ludox, destination=c_ludox.output_pin('samples'),
#                             amount=sbol3.Measure(100, tyto.OM.microliter))


# def measure_absorbance(protocol: paml.Protocol, plate, wavelength_param):
#     c_measure = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:D2')
#     return protocol.primitive_step(
#         'MeasureAbsorbance',
#         samples=c_measure.output_pin('samples'),
#         wavelength=wavelength_param,
#     )

LIBRARY_NAME = "pH_calibration"
PRIMITIVE_BASE_NAMESPACE = "https://bioprotocols.org/paml/primitives/"


def make_pH_meter_calibrated(protocol):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    pH_meter_calibrated_primitive = paml.Primitive("pHMeterCalibrated")
    pH_meter_calibrated_primitive.description = (
        "Determine if the pH Meter is calibrated."
    )
    pH_meter_calibrated_primitive.add_output(
        "return", "http://www.w3.org/2001/XMLSchema#boolean"
    )
    protocol.document.add(pH_meter_calibrated_primitive)

    sbol3.set_namespace(old_ns)

    def pH_meter_calibrated_compute_output(inputs, parameter):
        return uml.literal(True)

    pH_meter_calibrated_primitive.compute_output = (
        pH_meter_calibrated_compute_output
    )

    decision = protocol.make_decision_node(
        protocol.initial(),
        decision_input_behavior=pH_meter_calibrated_primitive,
    )
    return decision


def make_calibrate_pH_meter(protocol):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    pH_meter_calibrated = paml.Primitive("calibrate_pH_meter")
    pH_meter_calibrated.description = "Calibrate the pH meter."
    pH_meter_calibrated.add_output(
        "return", "http://www.w3.org/2001/XMLSchema#boolean"
    )
    protocol.document.add(pH_meter_calibrated)

    sbol3.set_namespace(old_ns)

    return protocol.execute_primitive("calibrate_pH_meter")


def resolve_value(v):
    if not isinstance(v, uml.LiteralReference):
        return v.value
    else:
        resolved = v.value.lookup()
        if isinstance(resolved, uml.LiteralSpecification):
            return resolved.value
        else:
            return resolved


def wrap_with_error_message(protocol, primitive, **kwargs):
    name = f"{primitive.display_id}_with_exception"
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)
    try:
        wrapped_primitive = paml.get_primitive(name=name, doc=protocol.document)
        if not wrapped_primitive:
            raise Exception("Need to create the primitive")
    except Exception as e:
        wrapped_primitive = paml.Primitive(name)
        wrapped_primitive.inherit_parameters(primitive)
        wrapped_primitive.add_output(
            "exception", "http://www.w3.org/2001/XMLSchema#string"
        )
        protocol.document.add(wrapped_primitive)
    sbol3.set_namespace(old_ns)

    wrapped_primitive_invocation = protocol.execute_primitive(
        wrapped_primitive, **kwargs
    )

    invocation_ok = protocol.make_decision_node(
        wrapped_primitive_invocation.output_pin("exception")
    )
    wrapped_primitive_error = make_error_message(
        protocol,
        message=wrapped_primitive_invocation.output_pin("exception"),
    )
    protocol.edges.append(
        uml.ControlFlow(source=wrapped_primitive_error, target=protocol.final())
    )
    invocation_ok.add_decision_output(
        protocol, paml.DECISION_ELSE, wrapped_primitive_error
    )

    return wrapped_primitive_invocation, invocation_ok


def make_inventorise_and_confirm_materials(protocol, reaction_volume):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    calculate_volume = paml.Primitive("calculate_volume")
    calculate_volume.description = "calculate_volume"
    calculate_volume.add_input("resource", sbol3.Component)
    calculate_volume.add_input("total_volume", tyto.OM.milliliter)
    calculate_volume.add_input("percentage", tyto.OM.milliliter)
    calculate_volume.add_output("volume", tyto.OM.milliliter)
    protocol.document.add(calculate_volume)

    def calculate_volume_compute_output(inputs, parameter):
        # X% weight/volume (g/mL) = (total_volume / 100) * X
        # return total_volume * percentage/100
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "total_volume":
                total_volume = resolve_value(value)
            elif i_parameter.name == "percentage":
                percentage = resolve_value(value)
        volume = sbol3.Measure(
            (total_volume * percentage) / 100.0, tyto.OM.milliliter
        )
        return uml.literal(volume)

    calculate_volume.compute_output = calculate_volume_compute_output

    sbol3.set_namespace(old_ns)

    reaction_vessel = protocol.execute_primitive(
        "EmptyContainer", specification="reaction_vessel"
    )
    reaction_vessel.name = "reaction_vessel"
    protocol.order(protocol.initial(), reaction_vessel)

    phosphoric_acid = create_phosphoric_acid()
    protocol.document.add(phosphoric_acid)
    ddh2o = create_h2o()
    protocol.document.add(ddh2o)
    naoh = create_naoh()
    protocol.document.add(naoh)

    naoh_container = protocol.execute_primitive(
        "EmptyContainer", specification="vial"
    )
    protocol.order(protocol.initial(), naoh_container)
    naoh_provision = protocol.execute_primitive(
        "Provision",
        resource=naoh,
        amount=sbol3.Measure(100, tyto.OM.milligram),
        destination=naoh_container.output_pin("samples"),
    )

    # 20% weight
    volume_phosphoric_acid = protocol.execute_primitive(
        "calculate_volume",
        resource=phosphoric_acid,
        total_volume=reaction_volume,
        percentage=20,
    )

    protocol.designate_output(
        "volume_phosphoric_acid",
        sbol3.OM_MEASURE,
        volume_phosphoric_acid.output_pin("volume"),
    )
    (
        provision_phosphoric_acid,
        provision_phosphoric_acid_error_handler,
    ) = wrap_with_error_message(
        protocol,
        paml.loaded_libraries["liquid_handling"].find("Provision"),
        resource=phosphoric_acid,
        destination=reaction_vessel.output_pin("samples"),
        amount=volume_phosphoric_acid.output_pin("volume"),
    )
    protocol.order(naoh_provision, provision_phosphoric_acid)

    # 80% weight
    volume_h2o = protocol.execute_primitive(
        "calculate_volume",
        resource=phosphoric_acid,
        total_volume=reaction_volume,
        percentage=80,
    )
    provision_h2o, provision_h2o_error_handler = wrap_with_error_message(
        protocol,
        paml.loaded_libraries["liquid_handling"].find("Provision"),
        resource=ddh2o,
        destination=reaction_vessel.output_pin("samples"),
        amount=volume_h2o.output_pin("volume"),
    )
    protocol.designate_output(
        "volume_h2o", sbol3.OM_MEASURE, volume_h2o.output_pin("volume")
    )
    provision_phosphoric_acid_error_handler.add_decision_output(
        protocol, None, provision_h2o
    )

    return reaction_vessel, provision_h2o_error_handler, naoh_container


def make_is_calibration_successful(protocol, primary_input_source):
    # old_ns = sbol3.get_namespace()
    # sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    # calibration_successful = paml.Primitive("calibrationSuccessful")
    # calibration_successful.description = "Determine if calibration worked."
    # calibration_successful.add_output(
    #     "return", "http://www.w3.org/2001/XMLSchema#boolean"
    # )
    # protocol.document.add(calibration_successful)

    # sbol3.set_namespace(old_ns)

    # def calibration_successful_output(inputs, parameter):
    #     return uml.literal(True)

    # calibration_successful.compute_output = calibration_successful_output

    decision = protocol.make_decision_node(primary_input_source)
    return decision


def make_mix(protocol, samples):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    mix_primitive = paml.Primitive("Mix")
    mix_primitive.description = "Mix contents of container."
    mix_primitive.add_input("samples", paml.SampleArray)
    mix_primitive.add_input("rpm", sbol3.Measure)

    protocol.document.add(mix_primitive)

    sbol3.set_namespace(old_ns)

    # Input RPM
    rpm = protocol.input_value(
        "rpm",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(
            100, tyto.NCIT.get_uri_by_term("Revolution per Minute")
        ),
    )
    protocol.designate_output(
        "rpm",
        sbol3.OM_MEASURE,
        rpm,
    )
    mix_invocation = protocol.execute_primitive("Mix", samples=samples, rpm=rpm)
    return mix_invocation


def make_stop_mix(protocol, samples):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)

    mix_primitive = paml.Primitive("StopMix")
    mix_primitive.description = "Stop Mixing contents of container."
    mix_primitive.add_input("samples", paml.SampleArray)

    protocol.document.add(mix_primitive)

    sbol3.set_namespace(old_ns)

    mix_invocation = protocol.execute_primitive("StopMix", samples=samples)
    return mix_invocation


def create_phosphoric_acid() -> sbol3.Component:
    h3po4 = sbol3.Component(
        "phosporic_acid", tyto.PubChem.get_uri_by_term("CID1004")
    )
    h3po4.name = "H3PO4: Phosphoric Acid"  # TODO get via tyto
    return h3po4


def create_h2o() -> sbol3.Component:
    ddh2o = sbol3.Component(
        "ddH2O", "https://identifiers.org/pubchem.substance:24901740"
    )
    ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"  # TODO get via tyto
    return ddh2o


def create_naoh() -> sbol3.Component:
    naoh = sbol3.Component("NaOH", tyto.PubChem.get_uri_by_term("CID14798"))
    naoh.name = "NaOH"  # TODO get via tyto
    return naoh


def make_error_message(protocol, message=None):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + LIBRARY_NAME)
    try:
        error_message = paml.get_primitive(
            name="error_message", doc=protocol.document
        )
        if not error_message:
            raise Exception("Need to create the primitive")
    except Exception as e:
        error_message = paml.Primitive("error_message")
        error_message.description = "Determine if calibration worked."
        error_message.add_input(
            "message", "http://www.w3.org/2001/XMLSchema#string"
        )
        protocol.document.add(error_message)
    sbol3.set_namespace(old_ns)

    return protocol.execute_primitive("error_message", message=message)


def pH_calibration_protocol() -> Tuple[paml.Protocol, Document]:
    #############################################
    # set up the document
    doc: Document = prepare_document()

    #############################################
    # Import the primitive libraries
    import_paml_libraries()

    #############################################
    # Create the protocol
    protocol: paml.Protocol = create_protocol()
    doc.add(protocol)

    # paml.import_library(LIBRARY_NAME)

    reaction_volume = protocol.input_value(
        "reaction_volume",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(10, tyto.OM.milliliter),
    )

    # 1. Decide whether to calibrate pH meter, and connect to initial node
    pH_meter_calibrated = make_pH_meter_calibrated(protocol)

    # 2. If not pH_meter_calibrated, then Calibrate the pH meter if needed
    calibrate_pH_meter = make_calibrate_pH_meter(protocol)
    # Link 1 -> 2 (False)
    pH_meter_calibrated.add_decision_output(protocol, False, calibrate_pH_meter)

    # 3. If pH_meter_calibrated, then inventorize and confirm materials
    (
        reaction_vessel,
        provision_h2o_error_handler,
        naoh_container,
    ) = make_inventorise_and_confirm_materials(protocol, reaction_volume)
    # Link 1 -> 3 (True)
    pH_meter_calibrated.add_decision_output(protocol, True, reaction_vessel)

    # 4. Decide whether calibration was successful
    is_calibration_successful = make_is_calibration_successful(
        protocol, calibrate_pH_meter.output_pin("return")
    )

    # Error Message Activity
    calibration_error = make_error_message(protocol, "Calibration Failed!")
    # Link 4 -> Error (False)
    is_calibration_successful.add_decision_output(
        protocol, False, calibration_error
    )

    # 5. Start Mix
    mix_vessel = make_mix(protocol, reaction_vessel.output_pin("samples"))
    provision_h2o_error_handler.add_decision_output(protocol, None, mix_vessel)

    # 6. Decide if ready to adjust
    ready_to_adjust = uml.MergeNode()
    protocol.nodes.append(ready_to_adjust)

    # Link 4 -> ready_to_adjust (True)
    is_calibration_successful.add_decision_output(
        protocol, True, ready_to_adjust
    )
    # Link 5 -> ready_to_adjust
    protocol.order(mix_vessel, ready_to_adjust)

    # 7. Adjustment subprotocol
    subprotocol: paml.Protocol = create_subprotocol(doc)

    subprotocol_invocation = protocol.execute_primitive(
        subprotocol,
        reaction_vessel=reaction_vessel,
        naoh_container=naoh_container,
    )
    # protocol.nodes.append(subprotocol)
    protocol.order(ready_to_adjust, subprotocol_invocation)

    # 8. Stop Mix
    stop_mix_vessel = make_stop_mix(
        protocol, reaction_vessel.output_pin("samples")
    )
    protocol.order(subprotocol_invocation, stop_mix_vessel)

    protocol.to_dot().view()
    return protocol, doc


if __name__ == "__main__":
    new_protocol: paml.Protocol
    new_protocol, doc = pH_calibration_protocol()
    print("Validating and writing protocol")
    v = doc.validate()
    assert len(v) == 0, "".join(f"\n {e}" for e in v)

    rdf_filename = os.path.join(
        os.path.dirname(__file__), "pH_calibration_protocol.nt"
    )
    doc.write(rdf_filename, sbol3.SORTED_NTRIPLES)
    print(f"Wrote file as {rdf_filename}")

    # render and view the dot
    dot = new_protocol.to_dot()
    dot.render(f"{new_protocol.name}.gv")
    dot.view()
