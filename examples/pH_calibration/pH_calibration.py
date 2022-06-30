"""
This script implements a pH calibration protocol that involves mixing Phosphoric Acid and water, and then adaptively adding NaOH until the solution reaches as target pH.  The protocols includes several cases for expected conditions, such as requiring pH meter re-calibration, failures in Provision steps, failures in the calibration process (i.e. unrecoverably exceeding the target pH), and failures in cleanup activities.  The primitives require custom implementations to support calculation of volumes and quantities, as well as defining decision point predicates.
"""


import importlib
import logging
import os
from os.path import basename
from typing import Tuple
from paml.execution_engine import ExecutionEngine

import examples.pH_calibration.ph_calibration_utils as util

import paml
# import paml_time as pamlt
import rdflib as rdfl
import sbol3
import tyto
import uml
from sbol3 import Document


logger: logging.Logger = logging.Logger("pH_calibration")

CONT_NS = rdfl.Namespace(
    "https://sift.net/container-ontology/container-ontology#"
)
OM_NS = rdfl.Namespace(
    "http://www.ontology-of-units-of-measure.org/resource/om-2/"
)

LIBRARY_NAME = "pH_calibration"
DOCSTRING = (
    "This protocol implements a pH calibration protocol with decision nodes."
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

    ############################################################################
    # Protocol Input Parameters
    ############################################################################
    (
        reaction_vessel,
        naoh_container,
        measurement_delay,
        initial_transfer_amount,
    ) = util.get_ph_adjustment_protocol_inputs(protocol)

    ############################################################################
    # Define Custom Primitives needed for protocol
    ############################################################################
    (
        measure_pH_primitive,
        measure_temperature_primitive,
        at_target_primitive,
        calculate_naoh_addition,
        error_message,
    ) = util.define_pH_adjustment_protocol_primitives(
        protocol.document, LIBRARY_NAME
    )

    ############################################################################
    # Protocol Steps
    ############################################################################

    # 7.1 Transfer NaOH into reaction vessel
    transfer = protocol.execute_primitive(
        "Transfer",
        source=naoh_container,
        destination=reaction_vessel,
        amount=initial_transfer_amount,
    )
    protocol.order(protocol.initial(), transfer)

    # 7.2 Wait X seconds (FIXME, need to implement)

    # 7.3 Measure pH
    measure_pH = protocol.execute_primitive(
        measure_pH_primitive, samples=reaction_vessel
    )
    # 7.4 Measure Temp
    measure_temp = protocol.execute_primitive(
        measure_temperature_primitive, samples=reaction_vessel
    )

    # Delay measurement
    # FIXME measurement_delay is an input parameter, but temporal constraints are instantiated at author time, rather than runtime.
    # wait_pH = pamlt.precedes(transfer, measurement_delay, measure_pH, units=measurement_delay.unit)
    protocol.order(transfer, measure_pH)
    # wait_temp = pamlt.precedes(transfer, measurement_delay.value, measure_temp, units=measurement_delay.unit)
    protocol.order(transfer, measure_temp)

    join_node = uml.JoinNode()
    protocol.nodes.append(join_node)
    protocol.order(measure_pH, join_node)
    protocol.order(measure_temp, join_node)

    # 7.5 At Target?

    at_target_decision = protocol.make_decision_node(
        join_node,
        decision_input_behavior=at_target_primitive,
        decision_input_source=measure_pH.output_pin("measurement"),
    )

    # At Target -> Yes: exit
    at_target_decision.add_decision_output(protocol, True, protocol.final())

    # At Target -> No: 7.6 calc next, goto Transfer
    calculate_naoh_addition_invocation = protocol.execute_primitive(
        calculate_naoh_addition,
        resource=naoh_container,
        temperature=measure_temp.output_pin("measurement"),
        pH=measure_pH.output_pin("measurement"),
        reaction_vessel=reaction_vessel,
    )
    # Edge into calculation
    at_target_decision.add_decision_output(
        protocol, False, calculate_naoh_addition_invocation
    )
    # Edge out of calculation
    protocol.edges.append(
        uml.ObjectFlow(
            source=calculate_naoh_addition_invocation.output_pin("return"),
            target=transfer.input_pin("amount"),
        )
    )

    # At Target -> Exception: No change, overshoot, overflow
    at_target_error = protocol.execute_primitive(
        error_message, message="Exception"
    )
    at_target_decision.add_decision_output(
        protocol, "Exception", at_target_error
    )
    protocol.edges.append(
        uml.ControlFlow(source=at_target_error, target=protocol.final())
    )

    # time_constraints = pamlt.TimeConstraints("pH Adjustment Timing",
    #                                             constraints=pamlt.And([wait_pH, wait_temp]),
    #                                             protocols=[protocol])
    # doc.add(time_constraints)

    return protocol


def create_setup_subprotocol(doc):
    logger.info("Creating setup_subprotocol")
    protocol: paml.Protocol = paml.Protocol("pH_adjustment_setup_protocol")
    protocol.name = "pH adjustment setup protocol"
    protocol.description = "pH adjustment setup protocol"
    doc.add(protocol)

    ############################################################################
    # Protocol Input Parameters
    ############################################################################
    (reaction_volume) = util.get_setup_protocol_inputs(protocol)

    ############################################################################
    # Protocol Materials
    ############################################################################

    (h3po4, ddh2o, naoh) = util.define_setup_protocol_materials(doc)

    ############################################################################
    # Define Custom Primitives needed for protocol
    ############################################################################
    calculate_volume_primitive = util.define_setup_protocol_primitives(
        protocol.document, LIBRARY_NAME
    )

    ############################################################################
    # Protocol Steps
    ############################################################################

    # 3.0
    reaction_vessel = protocol.execute_primitive(
        "EmptyContainer", specification="reaction_vessel"
    )
    reaction_vessel.name = "reaction_vessel"
    protocol.order(protocol.initial(), reaction_vessel)

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
        calculate_volume_primitive,
        resource=h3po4,
        total_volume=reaction_volume,
        percentage=20,
    )

    (
        provision_phosphoric_acid,
        provision_phosphoric_acid_error_handler,
    ) = util.wrap_with_error_message(
        protocol,
        LIBRARY_NAME,
        paml.loaded_libraries["liquid_handling"].find("Provision"),
        resource=h3po4,
        destination=reaction_vessel.output_pin("samples"),
        amount=volume_phosphoric_acid.output_pin("volume"),
    )

    # 80% weight
    volume_h2o = protocol.execute_primitive(
        calculate_volume_primitive,
        resource=h3po4,
        total_volume=reaction_volume,
        percentage=80,
    )
    (provision_h2o, provision_h2o_error_handler) = util.wrap_with_error_message(
        protocol,
        LIBRARY_NAME,
        paml.loaded_libraries["liquid_handling"].find("Provision"),
        resource=ddh2o,
        destination=reaction_vessel.output_pin("samples"),
        amount=volume_h2o.output_pin("volume"),
    )

    # Join all tokens before the final node
    final_join = uml.JoinNode()
    protocol.nodes.append(final_join)
    protocol.order(final_join, protocol.final())

    provision_phosphoric_acid_error_handler.add_decision_output(
        protocol, None, final_join
    )
    provision_h2o_error_handler.add_decision_output(
        protocol, None, final_join
    )

    protocol.designate_output(
        "naoh_container",
        paml.SampleArray,
        naoh_container.output_pin("samples"),
    )
    protocol.designate_output(
        "reaction_vessel",
        paml.SampleArray,
        reaction_vessel.output_pin("samples"),
    )
    protocol.designate_output(
        "volume_phosphoric_acid",
        sbol3.OM_MEASURE,
        volume_phosphoric_acid.output_pin("volume"),
    )
    protocol.designate_output(
        "volume_h2o", sbol3.OM_MEASURE, volume_h2o.output_pin("volume")
    )
    return protocol


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

    ############################################################################
    # Protocol Input Parameters
    ############################################################################

    (reaction_volume, rpm) = util.get_ph_calibration_protocol_inputs(protocol)

    ############################################################################
    # Define Custom Primitives needed for protocol
    ############################################################################
    (
        pH_meter_calibrated_primitive,
        calibrate_pH_meter_primitive,
        mix_primitive,
        stop_mix_primitive,
        clean_electrode_primitive,
    ) = util.define_pH_calibration_protocol_primitives(
        protocol.document, LIBRARY_NAME
    )

    ############################################################################
    # Protocol Steps
    ############################################################################

    # 1. Decide whether to calibrate pH meter, and connect to initial node
    pH_meter_calibrated = protocol.make_decision_node(
        protocol.initial(),
        decision_input_behavior=pH_meter_calibrated_primitive,
    )

    # 2. If not pH_meter_calibrated, then Calibrate the pH meter if needed
    calibrate_pH_meter = protocol.execute_primitive(
        calibrate_pH_meter_primitive
    )
    # Link 1 -> 2 (False)
    pH_meter_calibrated.add_decision_output(protocol, False, calibrate_pH_meter)

    # 3. If pH_meter_calibrated, then inventorize and confirm materials
    # (
    #     reaction_vessel,
    #     provision_h2o_error_handler,
    #     naoh_container,
    # ) = make_inventorise_and_confirm_materials(protocol, reaction_volume)


    # 3. Setup Reagents and Labware subprotocol
    setup_subprotocol: paml.Protocol = create_setup_subprotocol(doc)
    setup_subprotocol_invocation = protocol.execute_primitive(
        setup_subprotocol,
        reaction_volume=reaction_volume,
    )
    protocol.order(protocol.initial(), setup_subprotocol_invocation)

    # 4. Decide whether calibration was successful
    is_calibration_successful = decision = protocol.make_decision_node(
        calibrate_pH_meter.output_pin("return")
    )

    # 6. Decide if ready to adjust (Before 3.)
    ready_to_adjust1 = uml.MergeNode()
    protocol.nodes.append(ready_to_adjust1)
    protocol.order(setup_subprotocol_invocation, ready_to_adjust1)
    # Link 4 -> ready_to_adjust (True)
    is_calibration_successful.add_decision_output(
        protocol, True, ready_to_adjust1
    )
    ready_to_adjust2 = uml.MergeNode()
    protocol.nodes.append(ready_to_adjust2)
    protocol.order(setup_subprotocol_invocation, ready_to_adjust2)
    # Link 1 -> 3 (True)
    pH_meter_calibrated.add_decision_output(protocol, True, ready_to_adjust2)

    # Error Message Activity
    error_message_primitive = util.define_error_message(
        protocol.document, LIBRARY_NAME
    )
    calibration_error = protocol.execute_primitive(
        error_message_primitive, message="Calibration Failed!"
    )
    # Link 4 -> Error (False)
    is_calibration_successful.add_decision_output(
        protocol, False, calibration_error
    )

    # 5. Start Mix
    mix_vessel = protocol.execute_primitive(
        mix_primitive,
        samples=setup_subprotocol_invocation.output_pin("reaction_vessel"),
        rpm=rpm,
    )

    protocol.order(ready_to_adjust1, mix_vessel)
    protocol.order(ready_to_adjust2, mix_vessel)

    # 7. Adjustment subprotocol
    adjust_subprotocol: paml.Protocol = create_subprotocol(doc)

    adjust_subprotocol_invocation = protocol.execute_primitive(
        adjust_subprotocol,
        reaction_vessel=setup_subprotocol_invocation.output_pin("reaction_vessel"),
        naoh_container=setup_subprotocol_invocation.output_pin("naoh_container"),
        measurement_delay=sbol3.Measure(20, tyto.OM.second),
        initial_transfer_amount=sbol3.Measure(100, tyto.OM.milligram),
    )
    protocol.order(mix_vessel, adjust_subprotocol_invocation)

    # 8. Stop Mix
    stop_mix_vessel = protocol.execute_primitive(
        stop_mix_primitive, samples=setup_subprotocol_invocation.output_pin("reaction_vessel")
    )
    protocol.order(adjust_subprotocol_invocation, stop_mix_vessel)

    (
        clean_electrode_invocation,
        clean_electrode_error_handler,
    ) = util.wrap_with_error_message(
        protocol,
        LIBRARY_NAME,
        clean_electrode_primitive,
    )
    protocol.order(stop_mix_vessel, clean_electrode_invocation)
    clean_electrode_error_handler.add_decision_output(
        protocol, None, protocol.final()
    )

    protocol.designate_output(
        "rpm",
        sbol3.OM_MEASURE,
        rpm,
    )

    # protocol.to_dot().view()
    return protocol, doc


def reload():
    mainmodname = basename(__file__)[:-3]
    module = importlib.import_module(mainmodname)

    # reload the module to check for changes
    importlib.reload(module)
    # update the globals of __main__ with the any new or changed
    # functions or classes in the reloaded module
    globals().update(vars(module))
    main()


def main():
    new_protocol: paml.Protocol
    new_protocol, doc = pH_calibration_protocol()

    agent = sbol3.Agent("test_agent")
    ee = ExecutionEngine()
    parameter_values = [
        paml.ParameterValue(parameter=new_protocol.get_input("reaction_volume"), value=sbol3.Measure(10, tyto.OM.milliliter)),
    ]
    try:
        execution = ee.execute(new_protocol, agent, id="test_execution", parameter_values=parameter_values)
    except Exception as e:
        logger.exception(e)

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


if __name__ == "__main__":
    main()
