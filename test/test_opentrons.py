import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import sbol3

import labop
from build.lib.labop_convert.opentrons import opentrons_specialization
from labop.execution.execution_engine import ExecutionEngine
from labop.execution.harness import ProtocolSpecialization
from labop.utils.helpers import file_diff
from labop_convert.opentrons.opentrons_specialization import OT2Specialization

# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if "GH_TMPDIR" in os.environ:
    TMPDIR = os.environ["GH_TMPDIR"]
else:
    TMPDIR = tempfile.gettempdir()

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)


def load_protocol(protocol_def_fn, protocol_filename):
    loader = SourceFileLoader(protocol_def_fn, protocol_filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


CWD = os.path.split(os.path.realpath(__file__))[0]
protocol_def_file = os.path.join(
    CWD,
    "../examples/protocols/opentrons/opentrons-toy/opentrons_toy_protocol.py",
)
protocol_def = load_protocol("opentrons_toy_protocol", protocol_def_file)


class TestProtocolEndToEnd(unittest.TestCase):
    def create_protocol(
        self, doc: sbol3.Document, protocol: labop.Protocol
    ) -> labop.Protocol:
        protocol = labop.execution.harness.ProtocolLoader(
            protocol_def_file, "opentrons_toy_protocol"
        ).generate_protocol(doc, protocol)
        return protocol

    def test_create_protocol(self):
        harness = labop.execution.harness.ProtocolHarness(
            clean_output=True,
            base_dir=os.path.dirname(__file__),
            entry_point=self.create_protocol,
            agent="ot2_machine",
            execution_id="test_execution_1",
            namespace="https://labop.io/scratch/",
            protocol_name="OT2_demo",
            protocol_long_name="OT2 demo",
            protocol_description="Example Opentrons Protocol as LabOP",
            execution_kwargs={
                "use_ordinal_time": True,
                "failsafe": False,
            },
            artifacts=[
                ProtocolSpecialization(
                    specialization=OT2Specialization("opentrons_toy")
                ),
                labop.execution.harness.ProtocolExecutionRubric(
                    filename=os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        "testfiles",
                        "opentrons_toy.nt",
                    ),
                    # overwrite_rubric=True,  # Used to update rubric
                ),
            ],
        )

        harness.run(verbose=True)

        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )


if __name__ == "__main__":
    unittest.main()
