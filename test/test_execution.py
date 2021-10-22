import os
import tempfile
import unittest
import filecmp
import sbol3
import paml
import tyto
from paml.execution_engine import ExecutionEngine

import logging
l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class TestProtocolExecution(unittest.TestCase):
    def _compare_execution_line(self, line):
        """
        Return whether line satisfies a condition:
        1. Does not include a timepoint specification
        :param line:
        :return:
        """
        return "http://www.w3.org/ns/prov#startedAtTime" not in line and \
               "http://www.w3.org/ns/prov#endedAtTime" not in line

    def _compare_execution_files(self, fn1, fn2):
        with open(fn1, "r") as f1, open(fn2, "r") as f2:
            f1 = filter(self._compare_execution_line, f1.readlines())
            f2 = filter(self._compare_execution_line, f2.readlines())
            mismatches = [(x, y) for x, y in zip(f1, f2) if x != y]
            l.error(f"Executions in files: {fn1} and {fn2} have the following mismatches: \n{mismatches}")
            return len(mismatches) == 0

    def test_execute_protocol(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')

        protocol_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testfiles", "igem_ludox_test.nt")
        doc.read(protocol_file, 'nt')

        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")
        agent = sbol3.Agent("test_agent")

        # print('Importing libraries')
        # paml.import_library('liquid_handling')
        # print('... Imported liquid handling')

        ee = ExecutionEngine()
        parameter_values = [
            paml.ParameterValue(parameter=protocol.get_input("wavelength"), value=sbol3.Measure(100, tyto.OM.nanometer))
        ]
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        #dot = execution.to_dot()
        #dot.render(f'{protocol.name}.gv')
        #dot.view()  # uncomment to see it on your own screen

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        #temp_name = os.path.join(tempfile.gettempdir(), 'igem_ludox_test_exec.nt')
        #doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        #print(f'Wrote file as {temp_name}')

        #comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'igem_ludox_test_exec.nt')
        #doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        #print(f'Comparing against {comparison_file}')
        #assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        #assert self._compare_execution_files(temp_name, comparison_file), "Files are not identical"
        #print('File identical with test file')

    # def test_protocol_to_markdown(self):
    #     doc = sbol3.Document()
    #     doc.read('test/testfiles/igem_ludox_test.nt', 'nt')
    #     markdown.MarkdownConverter(doc).convert('iGEM_LUDOX_OD_calibration_2018')

    # Checking if files are identical needs to wait for increased stability
    # assert filecmp.cmp('iGEM_LUDOX_OD_calibration_2018.md','test/testfiles/iGEM_LUDOX_OD_calibration_2018.md')


if __name__ == '__main__':
    unittest.main()
