import os
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import labop
import labop_convert
from labop.execution.harness import ProtocolSpecialization


def fullpath(fname: str, path: str = "../examples/protocols/iGEM/") -> str:
    return os.path.join(os.path.dirname(__file__), f"{path}{fname}")


def load_protocol(protocol_filename, path="../examples/protocols/iGEM/"):
    testfile_path = fullpath(protocol_filename, path=path)
    module_name = protocol_filename.replace("-", "_")
    loader = SourceFileLoader(module_name, testfile_path)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


class TestIgemExamples(unittest.TestCase):
    def get_harness(
        self,
        filename: str,
        path: str = "../examples/protocols/iGEM/",
        use_custom_specialization: bool = True,
    ) -> labop.execution.harness.ProtocolHarness:
        out_dir = filename.split(".")[0].replace("-", "_")
        protocol_module = load_protocol(filename, path=path)
        if use_custom_specialization:
            specialization = protocol_module.InterlabCustomSpecialization(
                specialization=labop_convert.MarkdownSpecialization(
                    "test_LUDOX_markdown.md"
                )
            )
        else:
            specialization = ProtocolSpecialization(
                specialization=labop_convert.MarkdownSpecialization(
                    "test_LUDOX_markdown.md"
                )
            )

        harness = labop.execution.harness.ProtocolHarness(
            clean_output=True,
            protocol_name=out_dir,
            base_dir=os.path.join(os.path.dirname(__file__), "out", out_dir),
            entry_point=protocol_module.generate_protocol,
            agent="test_agent",
            libraries=[
                "liquid_handling",
                "plate_handling",
                "spectrophotometry",
                "sample_arrays",
                "culturing",
            ],
            artifacts=[specialization],
            execution_kwargs={
                "sample_format": "json",
                "track_samples": False,
            },
            execution_id="test_execution",
        )
        return harness

    def test_example1(self):
        harness = self.get_harness("interlab-endpoint.py")
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )

    def test_example2(self):
        harness = self.get_harness("interlab-exp1.py")
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )

    def test_example3(self):
        harness = self.get_harness("interlab-exp2.py")
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )

    def test_example4(self):
        harness = self.get_harness("interlab-exp3_challenge.py")
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )

    def test_example5(self):
        harness = self.get_harness(
            "multicolor-particle-calibration.py",
            path="../examples/protocols/calibration/multicolor-particle-calibration/",
            use_custom_specialization=False,
        )
        harness.run()
        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )


if __name__ == "__main__":
    unittest.main()
