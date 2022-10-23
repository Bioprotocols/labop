import filecmp
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import logging
import os
import tempfile
import unittest
import sbol3
import labop

from labop.execution_engine import ExecutionEngine
from labop_convert.opentrons.opentrons_specialization import OT2Specialization


# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if "GH_TMPDIR" in os.environ:
    TMPDIR = os.environ["GH_TMPDIR"]
else:
    TMPDIR = tempfile.gettempdir()


def load_protocol(protocol_def_fn, protocol_filename):
    loader = SourceFileLoader(protocol_def_fn, protocol_filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


CWD = os.path.split(os.path.realpath(__file__))[0]
protocol_def_file = os.path.join(CWD, "../examples/opentrons_toy_protocol.py")
protocol_def = load_protocol("opentrons_toy_protocol", protocol_def_file)

out_dir = os.path.join(CWD, "out")
if not os.path.exists(out_dir):
    os.mkdir(out_dir)


class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol: labop.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("LUDOX_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = protocol_def.opentrons_toy_protocol()

        protocol.to_dot().render(
            filename=os.path.join(out_dir, protocol.display_name), format="png"
        )

        agent = sbol3.Agent("ot2_machine", name="OT2 machine")

        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(
            use_ordinal_time=True,
            specializations=[
                OT2Specialization(os.path.join(out_dir, "opentrons_toy"))
            ],
        )
        parameter_values = []
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution_1",
            parameter_values=parameter_values,
        )

        ########################################
        # Validate and write the document

        print("Validating and writing protocol")
        v = doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        nt_file = "opentrons_toy.nt"
        temp_name = os.path.join(TMPDIR, nt_file)

        # At some point, rdflib began inserting an extra newline into
        # N-triple serializations, which breaks file comparison.
        # Here we strip extraneous newlines, to maintain reverse compatibility
        with open(temp_name, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Wrote file as {temp_name}")

        comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            nt_file,
        )
        # with open(comparison_file, 'w') as f:
        #     f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Comparing against {comparison_file}")
        assert filecmp.cmp(
            temp_name, comparison_file
        ), "Files are not identical"
        print("File identical with test file")


if __name__ == "__main__":
    unittest.main()
