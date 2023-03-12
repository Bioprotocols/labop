import os
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import sbol3


def fullpath(fname: str) -> str:
    return os.path.join(os.path.dirname(__file__), f"../examples/{fname}")


def load_protocol(protocol_filename):
    testfile_path = fullpath(protocol_filename)
    module_name = protocol_filename.replace("-", "_")
    loader = SourceFileLoader(module_name, testfile_path)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


class TestIgemExamples(unittest.TestCase):
    def test_example1(self):
        load_protocol("interlab-endpoint.py")

    def test_example2(self):
        load_protocol("interlab-exp1.py")

    def test_example3(self):
        load_protocol("interlab-exp2.py")

    def test_example4(self):
        load_protocol("interlab-exp3_challenge.py")

    def test_example5(self):
        load_protocol(
            "protocols/multicolor-particle-calibration/multicolor-particle-calibration.py"
        )


if __name__ == "__main__":
    unittest.main()
