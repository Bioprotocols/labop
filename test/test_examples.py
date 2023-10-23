import glob
import logging
import os
import re
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from types import ModuleType
from typing import List

from parameterized import parameterized

from labop.execution import ProtocolHarness

l = logging.Logger(__file__)
l.setLevel(logging.INFO)


def load_protocol(testfile_path) -> ModuleType:
    module_name = testfile_path.rsplit("/", 1)[1].rsplit(".py")[0].replace("-", "_")
    loader = SourceFileLoader(module_name, testfile_path)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


def discover_example_protocols(example_directory: str) -> List[str]:
    candidate_protocols = glob.glob(f"{example_directory}/**/*py", recursive=True)
    actual_protocols = []
    for p in candidate_protocols:
        with open(p, "r") as f:
            lines = f.readlines()
            try:
                if next(l for l in lines if re.match(".*Protocol\(.*\)", l)):
                    actual_protocols.append(p)
            except:
                # Cannot find a Protocol
                continue
    return actual_protocols


example_directory = os.path.join(os.path.dirname(__file__), f"../examples/")
test_files = discover_example_protocols(example_directory)
expected_failures = {
    "../examples/protocols/pcr_pylabrobot/pcr_pylabrobot.py": {
        "description": "Fails because there is a missing primer layout csv."
    },
    "../examples/protocols/opentrons/opentrons-pcr/opentrons_pcr_example.py": {
        "description": "Fails because there is a missing primer layout csv."
    },
    "../examples/protocols/pH_calibration/pH_calibration.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/interlab-timepoint-B_AV.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/interlab-exp1_MI.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/interlab-growth-curve.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/interlab-exp2_MI.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/revised-interlab-growth-curve.py": {
        "description": "Fails due to several well-formedness errors"
    },
    "../examples/protocols/iGEM/interlab-timepoint-B.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/interlab-exp2_from1.py": {
        "description": "Fails because it cannot import module."
    },
    "../examples/protocols/iGEM/challenging-interlab-growth-curve.py": {
        "description": "Fails due to several well-formedness errors"
    },
}


class TestModels(unittest.TestCase):
    @parameterized.expand(test_files)
    def test_protocol(self, test_file):
        test_file_abs_path = test_file.split(os.path.dirname(__file__))[1][1:]
        try:
            module = load_protocol(test_file)
            model_protocol_harnesses = {
                k: v
                for k, v in module.__dict__.items()
                if isinstance(v, ProtocolHarness)
            }
            output_base_dir = os.path.join(
                os.path.dirname(__file__),
                "out",
                test_file_abs_path.split("../examples/protocols/")[1].split(".py")[0],
            )
            for id, harness in model_protocol_harnesses.items():
                l.info(f"Running ProtocolHarness '{id}' ...")
                harness.run(base_dir=output_base_dir)
        except Exception as e:
            assert (
                test_file_abs_path in expected_failures
            ), f"({test_file}) Example unexpectedly failed: {e}"
            l.info(
                f"({test_file}) Example failed as expected: {expected_failures[test_file_abs_path]['description']}"
            )


if __name__ == "__main__":
    unittest.main()
