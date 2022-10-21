import filecmp
import logging
import os
import tempfile
import unittest

import sbol3

import uml
import labop
from labop.execution_engine import ExecutionEngine


# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if 'GH_TMPDIR' in os.environ:
    TMPDIR = os.environ['GH_TMPDIR']
else:
    TMPDIR = tempfile.gettempdir()

class TestProtocolEndToEnd(unittest.TestCase):

    def test_create_protocol(self):
        protocol: labop.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("decision_protocol")
        logger.setLevel(logging.INFO)
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')
        protocol = labop.Protocol("decision_node_test")
        doc.add(protocol)

        initial = protocol.initial()
        final = protocol.final()

        pH_meter_calibrated = labop.Primitive('pHMeterCalibrated')
        pH_meter_calibrated.description = 'Determine if the pH Meter is calibrated.'
        pH_meter_calibrated.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
        doc.add(pH_meter_calibrated)

        def pH_meter_calibrated_compute_output(inputs, parameter, sample_format):
            return uml.literal(True)
        pH_meter_calibrated.compute_output = pH_meter_calibrated_compute_output

        decision = protocol.make_decision_node(
            initial,  # primary_incoming
            decision_input_behavior = pH_meter_calibrated,
            decision_input_source = None,
            outgoing_targets = [ (uml.literal(True), final), (uml.literal(False), final) ])

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(use_ordinal_time=True, use_defined_primitives=False)
        parameter_values = []
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)


        temp_name = os.path.join(TMPDIR, 'decision_node_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'decision_node_test.nt')
        # doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
