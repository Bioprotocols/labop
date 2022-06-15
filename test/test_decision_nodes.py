import filecmp
import logging
import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec
from typing import List, Tuple

import sbol3

import paml
from paml.execution_engine import ExecutionEngine
import uml

class TestProtocolEndToEnd(unittest.TestCase):

    def test_create_protocol(self):
        protocol: paml.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("decision_protocol")
        logger.setLevel(logging.INFO)
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')
        protocol = paml.Protocol("decision_node_test")
        doc.add(protocol)

        initial = protocol.initial()
        final = protocol.final()

        # paml.import_library('pH_measurement')
        # logger.info('... Imported pH measurement handling')
        # pH_ok_behavior = paml.get_primitive(doc, "MeasurePH")



        allocate_equipment = paml.Primitive('AllocateEquipment')
        allocate_equipment.description = 'Allocate a piece of equipment.'
        allocate_equipment.add_input('specification', 'http://www.w3.org/2001/XMLSchema#boolean')
        allocate_equipment.add_output('resource', 'http://bioprotocols.org/sbol#Identified')
        doc.add(allocate_equipment)
        meter = protocol.primitive_step('AllocateEquipment', specification="meter1")

        pH_meter_calibrated = paml.Primitive('pHMeterCalibrated')
        pH_meter_calibrated.description = 'Determine if the pH Meter is calibrated.'
        pH_meter_calibrated.add_input('decision_input', 'http://bioprotocols.org/sbol#Identified')
        pH_meter_calibrated.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
        doc.add(pH_meter_calibrated)


        def pH_meter_calibrated_compute_output(inputs, parameter):
            return uml.literal(True)
        pH_meter_calibrated.compute_output = pH_meter_calibrated_compute_output

        decision_input = protocol.primitive_step('pHMeterCalibrated', decision_input=meter.output_pin("resource"))

        decision_input_flow = uml.ObjectFlow(source=decision_input.output_pin("return"))
        protocol.edges.append(decision_input_flow)

        primary_incoming = uml.ControlFlow(source=initial)
        protocol.edges.append(primary_incoming)

        outgoing_targets = [
                uml.ControlFlow(guard=uml.literal(True), target=final),  # Guard and destination node
                uml.ControlFlow(guard=uml.literal(False), target=final)  # Guard and destination node
            ]

        # decision = protocol.make_decision_node(
        #     primary_incoming,  # primary_incoming
        #     decision_input = pH_meter_calibrated,
        #     decision_input_flow = decision_input_flow,
        #     outgoing_targets = outgoing_targets
        # )
        decision = uml.DecisionNode(decision_input=decision_input,
                                    decision_input_flow=decision_input_flow)
        protocol.nodes.append(decision)
        decision_input_flow.target = decision
        primary_incoming.target = decision
        for outgoing_target in outgoing_targets:
            outgoing_target.source = decision
            protocol.edges.append(outgoing_target)

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine()
        parameter_values = []
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), 'decision_node_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'decision_node_test.nt')
        doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
