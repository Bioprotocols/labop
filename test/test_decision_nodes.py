import logging
import os
import tempfile
import unittest

import sbol3

# from labop.utils.helpers import file_diff
import labop
from labop.execution.harness import (
    ProtocolExecutionRubric,
    ProtocolHarness,
    ProtocolLoader,
)
from uml import ActivityParameterNode, CallBehaviorAction, InputPin

# OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
# if not os.path.exists(OUT_DIR):
#     os.mkdir(OUT_DIR)

# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if "GH_TMPDIR" in os.environ:
    TMPDIR = os.environ["GH_TMPDIR"]
else:
    TMPDIR = tempfile.gettempdir()


protocol_def_file = os.path.join(
    os.path.dirname(__file__), "../examples/protocols/ludox/LUDOX_protocol.py"
)


class TestProtocolEndToEnd(unittest.TestCase):
    def create_protocol(self, doc: sbol3.Document, protocol: labop.Protocol):
        logger = logging.getLogger("decision_protocol")
        logger.setLevel(logging.INFO)

        initial = protocol.initial()
        final = protocol.final()

        pH_meter_calibrated = labop.Primitive("pHMeterCalibrated")
        pH_meter_calibrated.description = "Determine if the pH Meter is calibrated."
        pH_meter_calibrated.add_output(
            "return", "http://www.w3.org/2001/XMLSchema#boolean"
        )
        doc.add(pH_meter_calibrated)

        def pH_meter_calibrated_compute_output(
            inputs, parameter, sample_format, record_hash
        ):
            return True

        pH_meter_calibrated.compute_output = pH_meter_calibrated_compute_output

        decision = protocol.make_decision_node(
            initial,  # primary_incoming
            decision_input_behavior=pH_meter_calibrated,
            # decision_input_source=pH_meter_calibrated.get_output("return"),
            outgoing_targets=[
                (True, final),
                (False, final),
            ],
        )

        return protocol

    def generate_ludox_calibration_decision(
        self, doc: sbol3.Document, protocol: labop.Protocol
    ) -> labop.Protocol:
        logger = logging.getLogger("LUDOX_decision_protocol")
        logger.setLevel(logging.INFO)

        protocol = ProtocolLoader(
            protocol_def_file, "ludox_protocol"
        ).generate_protocol(doc, protocol)

        measurment_is_nominal = labop.Primitive("measurementNominal")
        measurment_is_nominal.description = (
            "Determine if the measurments are acceptable."
        )
        measurment_is_nominal.add_input("decision_input", labop.SampleData)
        measurment_is_nominal.add_output(
            "return", "http://www.w3.org/2001/XMLSchema#boolean"
        )
        doc.add(measurment_is_nominal)

        def measurement_is_nominal_compute_output(
            inputs, parameter, sample_format, record_hash
        ):
            return True

        measurment_is_nominal.compute_output = measurement_is_nominal_compute_output

        try:
            measure = next(
                iter(
                    [
                        n
                        for n in protocol.nodes
                        if isinstance(n, CallBehaviorAction)
                        and n.behavior
                        == "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance"
                    ]
                )
            )
            #  measure.add_output(
            #         "error", "http://www.w3.org/2001/XMLSchema#boolean"
            #     )
            measurement_samples = next(
                iter(
                    [
                        e.get_source()
                        for e in protocol.edges
                        if measure.identity in e.target
                        and isinstance(e.get_target(), InputPin)
                        and e.get_target().name == "samples"
                    ]
                )
            )
            wavelength_param = next(
                iter(
                    [n for n in protocol.nodes if isinstance(n, ActivityParameterNode)]
                )
            )
        except StopIteration as e:
            raise Exception("Could not find MeasureAbsorbance in protocol")

        # output = protocol.designate_output(
        #     "calibration_nominal",
        #     "http://www.w3.org/2001/XMLSchema#boolean",
        #     None,
        # )

        measure2 = protocol.primitive_step(
            "MeasureAbsorbance",
            samples=measurement_samples,
            wavelength=wavelength_param,
        )
        protocol.order(measure2, protocol.final())

        output1 = protocol.designate_output(
            "absorbance_redo",
            sbol3.OM_MEASURE,
            measure2.output_pin("measurements"),
        )

        # primary incoming node is a measurement primitive (because its not a control node, the primary incoming edge is an object flow)
        # The protocol is getting two object edges into the decision node (from the measurement and its output pin).  There should not be an object edge from the measurement.  The outputs are object flows, but are used as control flows.
        decision = protocol.make_decision_node(
            # The first parameter is the primary_incoming activity passing control flow through the decision
            measure,  # .output_pin("measurements"),  # primary_incoming
            # The decision input behavior is the behavior used to select the flow of the decision node
            decision_input_behavior=measurment_is_nominal,
            # The decision input source determines the object flow that influences the decision input behavior output
            decision_input_source=measure.output_pin("measurements"),
            outgoing_targets=[
                (True, protocol.final()),
                (False, measure2),
            ],
        )
        return protocol

    def test_create_protocol(self):
        namespace = "https://bbn.com/scratch/"
        harness = ProtocolHarness(
            clean_output=True,
            base_dir=os.path.join(
                os.path.dirname(__file__), "out", "out_create_protocol"
            ),
            namespace=namespace,
            execution_id="test_execution",
            protocol_name="decision_node_test",
            protocol_long_name=None,
            protocol_description=None,
            entry_point=self.create_protocol,
            agent="test_agent",
            execution_kwargs={
                "use_ordinal_time": True,
                "use_defined_primitives": False,
            },
            artifacts=[
                ProtocolExecutionRubric(
                    filename=os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        "testfiles",
                        "decision_node_test.nt",
                    ),
                    overwrite_rubric=True,  # Used to update rubric
                )
            ],
        )
        harness.run(verbose=True)

        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )

        # execution_artifact = harness.execution_artifact()
        # protocol_artifact = execution_artifact.protocol_artifact

        # agent = sbol3.Agent("test_agent")
        # ee = ExecutionEngine(
        #     out_dir=OUT_DIR, use_ordinal_time=True, use_defined_primitives=False
        # )
        # parameter_values = []
        # execution = ee.execute(
        #     protocol,
        #     agent,
        #     id="test_execution",
        #     parameter_values=parameter_values,
        # )

    def test_ludox_calibration_decision(self):
        harness = ProtocolHarness(
            clean_output=True,
            base_dir=os.path.join(
                os.path.dirname(__file__), "out", "out_calibration_decision"
            ),
            entry_point=self.generate_ludox_calibration_decision,
            artifacts=[],
        )
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )


if __name__ == "__main__":
    unittest.main()
