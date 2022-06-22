"""This module supports the pH_calibration.py script by defining several of the primitives and other related helpers, such as error handlers.
"""
import sbol3
import paml
import uml
import tyto
from paml.primitive_execution import declare_primitive, resolve_value

from typing import Tuple

def get_ph_adjustment_protocol_inputs(
    protocol: paml.Protocol,
) -> Tuple[uml.ActivityParameterNode]:
    """Declare and return the inputs for the pH adjustment protocol.

    Args:
        protocol (paml.Protocol): protocol receiving inputs

    Returns:
        Tuple[uml.ActivityParameterNode]: protocol inputs
    """
    reaction_vessel = protocol.input_value(
        "reaction_vessel",
        paml.SampleArray,
    )

    naoh_container = protocol.input_value(
        "naoh_container",
        paml.SampleArray,
    )

    measurement_delay = protocol.input_value(
        "measurement_delay",
        sbol3.Measure,
        default_value=sbol3.Measure(10, tyto.OM.second),
        optional=True,
    )

    return reaction_vessel, naoh_container, measurement_delay

def define_pH_adjustment_protocol_primitives(
    document: sbol3.Document, library: str
):
    measure_pH_primitive = declare_primitive(
        document,
        library,
        "MeasurePH",
        inputs=[{"name": "samples", "type": paml.SampleArray}],
        outputs=[{"name": "measurement", "type": paml.SampleData}],
        description="Measure pH of samples.",
    )

    measure_temperature_primitive = declare_primitive(
        document,
        library,
        "MeasureTemperature",
        inputs=[{"name": "samples", "type": paml.SampleArray}],
        outputs=[{"name": "measurement", "type": paml.SampleData}],
        description="Measure Temperature of samples.",
    )

    at_target_primitive = declare_primitive(
        document,
        library,
        "AtTargetPH",
        inputs=[{"name": "decision_input", "type": paml.SampleData}],
        outputs=[
            {
                "name": "return",
                "type": "http://www.w3.org/2001/XMLSchema#boolean",
            }
        ],
        description="Determine if pH meets target pH",
    )

    def at_target_compute_output(inputs, parameter):
        # X% weight/volume (g/mL) = (total_volume / 100) * X
        # return total_volume * percentage/100
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "measurement":
                measurement = resolve_value(value)
        # FIXME write predicate test
        # volume = sbol3.Measure(
        #     (total_volume * percentage) / 100.0, tyto.OM.milliliter
        # )
        return uml.literal(True)

    at_target_primitive.compute_output = at_target_compute_output

    calculate_naoh_addition = declare_primitive(
        document,
        library,
        "CalculateNaOHAddition",
        inputs=[
            {"name": "resource", "type": sbol3.Component},
            {"name": "temperature", "type": "http://www.ontology-of-units-of-measure.org/resource/om-2/degreeCelsius"},
            {"name": "pH", "type": "http://www.w3.org/2001/XMLSchema#float"},
            {"name": "reaction_vessel", "type": paml.SampleArray},
        ],
        outputs=[{"name": "return", "type": tyto.OM.milligram}],
        description="Calculate NaOH Addition",
    )

    def calculate_naoh_addition_output(inputs, parameter):
        # X% weight/volume (g/mL) = (total_volume / 100) * X
        # return total_volume * percentage/100
        # for input in inputs:
        #     i_parameter = input.parameter.lookup().property_value
        #     value = input.value
        #     if i_parameter.name == "total_volume":
        #         total_volume = resolve_value(value)
        #     elif i_parameter.name == "percentage":
        #         percentage = resolve_value(value)
        # volume = sbol3.Measure(
        #     (total_volume * percentage) / 100.0, tyto.OM.milliliter
        # )
        return sbol3.Measure(100, tyto.OM.milligram)  # uml.literal(volume)

    calculate_naoh_addition.compute_output = calculate_naoh_addition_output

    error_message = define_error_message(document, library)


    return (
        measure_pH_primitive,
        measure_temperature_primitive,
        at_target_primitive,
        calculate_naoh_addition,
        error_message
    )

def define_error_message(document: sbol3.Document, library: str):
    return declare_primitive(
                document,
                library,
                "ErrorMessage",
                inputs=[
                    {"name": "message", "type": "http://www.w3.org/2001/XMLSchema#string"},
                ],
                description="Display an Error Message",
            )

def wrap_with_error_message(protocol, library, primitive, **kwargs):
    name = f"{primitive.display_id}_with_exception"

    wrapped_primitive = declare_primitive(
                protocol.document,
                library,
                name,
                template=primitive,
                outputs=[
                    {"name": "error", "type": "http://www.w3.org/2001/XMLSchema#string"},
                ],
                description=f"Extends {primitive} with an error output pin",
            )

    wrapped_primitive_invocation = protocol.execute_primitive(
        wrapped_primitive, **kwargs
    )

    invocation_ok = protocol.make_decision_node(
        wrapped_primitive_invocation.output_pin("error")
    )
    error_message_primitive = define_error_message(protocol.document, library)
    error_message_invocation = protocol.execute_primitive(error_message_primitive,
        message=wrapped_primitive_invocation.output_pin("error"),
    )
    protocol.edges.append(
        uml.ControlFlow(source=error_message_invocation, target=protocol.final())
    )
    invocation_ok.add_decision_output(
        protocol, paml.DECISION_ELSE, error_message_invocation
    )

    return wrapped_primitive_invocation, invocation_ok

def get_ph_calibration_protocol_inputs(protocol: paml.Protocol,
) -> Tuple[uml.ActivityParameterNode]:
    """Declare and return the inputs for the pH calibration protocol.

    Args:
        protocol (paml.Protocol): protocol receiving inputs

    Returns:
        Tuple[uml.ActivityParameterNode]: protocol inputs
    """
    reaction_volume = protocol.input_value(
        "reaction_volume",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(10, tyto.OM.milliliter),
    )

    rpm = protocol.input_value(
        "rpm",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(
            100,
            # tyto.NCIT.get_uri_by_term("Revolution per Minute")
            "https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&version=21.10d&code=C70469&ns=ncit"
        ),
    )
    return (reaction_volume, rpm)

def define_pH_calibration_protocol_primitives(
    document: sbol3.Document, library: str
):
    pH_meter_calibrated_primitive = declare_primitive(
        document,
        library,
        "PHMeterCalibrated",
        outputs=[{"name": "return", "type": "http://www.w3.org/2001/XMLSchema#boolean"}],
        description="Decide whether to calibrate pH meter.",
    )

    def pH_meter_calibrated_compute_output(inputs, parameter):
        return uml.literal(True)
    pH_meter_calibrated_primitive.compute_output = (
        pH_meter_calibrated_compute_output
    )

    calibrate_pH_meter_primitive = declare_primitive(
        document,
        library,
        "CalibratePHMeter",
        outputs=[{"name": "return", "type": "http://www.w3.org/2001/XMLSchema#boolean"}],
        description="Calibrate the pH meter.",
    )

    mix_primitive = declare_primitive(
        document,
        library,
        "Mix",
        inputs=[{"name": "samples", "type": paml.SampleArray},
        {"name": "rpm", "type": sbol3.Measure},],
        description="Start Mixing contents of container.",
    )

    stop_mix_primitive = declare_primitive(
        document,
        library,
        "StopMix",
        inputs=[{"name": "samples", "type": paml.SampleArray},
        ],
        description="Stop Mixing contents of container.",
    )

    clean_electrode_primitive = declare_primitive(
        document,
        library,
        "CleanElectrode",
        description="Clean the pH meter electrode",
    )


    return (
        pH_meter_calibrated_primitive,
        calibrate_pH_meter_primitive,
        mix_primitive,
        stop_mix_primitive,
        clean_electrode_primitive
    )

def define_setup_protocol_primitives(
    document: sbol3.Document, library: str
):
    calculate_volume_primitive = declare_primitive(
        document,
        library,
        "CalculateVolume",
        inputs=[
            {"name": "resource", "type": sbol3.Component},
            {"name": "total_volume", "type": tyto.OM.milliliter},
            {"name": "percentage", "type": "http://www.w3.org/2001/XMLSchema#float"},
        ],
        outputs=[{"name": "volume", "type": tyto.OM.milliliter}],
        description="Decide whether to calibrate pH meter.",
    )
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
            (total_volume.value * percentage) / 100.0, tyto.OM.milliliter
        )
        return uml.literal(volume)
    calculate_volume_primitive.compute_output = calculate_volume_compute_output



    return calculate_volume_primitive

def define_setup_protocol_materials(document):
    h3po4 = sbol3.Component(
        "phosporic_acid", tyto.PubChem.get_uri_by_term("CID1004")
    )
    h3po4.name = "H3PO4: Phosphoric Acid"
    document.add(h3po4)

    ddh2o = sbol3.Component(
        "ddH2O", "https://identifiers.org/pubchem.substance:24901740"
    )
    ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"
    document.add(ddh2o)

    naoh = sbol3.Component("NaOH", tyto.PubChem.get_uri_by_term("CID14798"))
    naoh.name = "NaOH"
    document.add(naoh)

    return (
        h3po4,
        ddh2o,
        naoh
    )

def get_setup_protocol_inputs(protocol: paml.Protocol,
) -> Tuple[uml.ActivityParameterNode]:
    """Declare and return the inputs for the pH calibration protocol.

    Args:
        protocol (paml.Protocol): protocol receiving inputs

    Returns:
        Tuple[uml.ActivityParameterNode]: protocol inputs
    """
    reaction_volume = protocol.input_value(
        "reaction_volume",
        sbol3.OM_MEASURE,
        optional=True,
        default_value=sbol3.Measure(10, tyto.OM.milliliter),
    )

    return reaction_volume
