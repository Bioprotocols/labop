import datetime
import filecmp
import logging
import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec

import sbol3
import paml
from paml.execution_engine import ExecutionEngine
import uml
import tyto

protocol_def_file = os.path.join(os.path.dirname(__file__), '../examples/LUDOX_protocol.py')


def load_ludox_protocol(protocol_filename):
    loader = SourceFileLoader('ludox_protocol', protocol_filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


protocol_def = load_ludox_protocol(protocol_def_file)


class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol: paml.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("LUDOX_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = protocol_def.ludox_protocol()

        ########################################
        # Validate and write the document

        agent = sbol3.Agent("test_agent")


        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(use_ordinal_time=True)
        parameter_values = [
            paml.ParameterValue(parameter=protocol.get_input("wavelength"),
                                value=uml.LiteralIdentified(value=sbol3.Measure(100, tyto.OM.nanometer)))
        ]
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        # Get the SampleData objects and attach values
        # get_data() returns a dict of output parameter ids to SampleData objects
        data = execution.get_data()

        for k, v in data.items():
            my_df = v.to_dataframe()  # Get the empty dataframe for SampleData
            my_df["values"] = my_df["values"].apply(lambda x: 8)  # Fill data with dummy value of 8
            v.values = my_df.to_csv(sep=",")  # Store values in SampleData


        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), 'igem_ludox_data_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'igem_ludox_data_test.nt')
        # doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
