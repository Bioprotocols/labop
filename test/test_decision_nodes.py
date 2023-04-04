import filecmp
import logging
import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import sbol3

from labop import ExecutionEngine, Primitive, Protocol, SampleData
from uml import ActivityParameterNode, CallBehaviorAction, InputPin

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if "GH_TMPDIR" in os.environ:
    TMPDIR = os.environ["GH_TMPDIR"]
else:
    TMPDIR = tempfile.gettempdir()


protocol_def_file = os.path.join(
    os.path.dirname(__file__), "../examples/LUDOX_protocol.py"
)


def load_ludox_protocol(protocol_filename):
    loader = SourceFileLoader("ludox_protocol", protocol_filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


protocol_def = load_ludox_protocol(protocol_def_file)


class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol: Protocol
        doc: sbol3.Document
        logger = logging.getLogger("decision_protocol")
        logger.setLevel(logging.INFO)
        doc = sbol3.Document()
        sbol3.set_namespace("https://bbn.com/scratch/")
        protocol = Protocol("decision_node_test")
        doc.add(protocol)

        initial = protocol.initial()
        final = protocol.final()

        pH_meter_calibrated = Primitive("pHMeterCalibrated")
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

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            out_dir=OUT_DIR, use_ordinal_time=True, use_defined_primitives=False
        )
        parameter_values = []
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution",
            parameter_values=parameter_values,
        )

        ########################################
        # Validate and write the document
        print("Validating and writing protocol")
        v = doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        temp_name = os.path.join(TMPDIR, "decision_node_test.nt")
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f"Wrote file as {temp_name}")

        comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "decision_node_test.nt",
        )
        # doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f"Comparing against {comparison_file}")
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print("File identical with test file")

    def test_ludox_calibration_decision(self):
        protocol: Protocol
        doc: sbol3.Document
        logger = logging.getLogger("LUDOX_decision_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = protocol_def.ludox_protocol()

        measurment_is_nominal = Primitive("measurementNominal")
        measurment_is_nominal.description = (
            "Determine if the measurments are acceptable."
        )
        measurment_is_nominal.add_input("decision_input", SampleData)
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
                        and isinstance(e.target.lookup(), InputPin)
                        and e.target.lookup().name == "samples"
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
        decision = protocol.make_decision_node(
            measure,  # .output_pin("measurements"),  # primary_incoming
            decision_input_behavior=measurment_is_nominal,
            decision_input_source=measure.output_pin("measurements"),
            outgoing_targets=[
                (True, protocol.final()),
                (False, measure2),
            ],
        )
        # protocol.to_dot().view()


if __name__ == "__main__":
    unittest.main()
