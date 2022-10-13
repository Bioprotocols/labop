import unittest

import tyto
import paml
import uml
import sbol3
import paml
from paml.execution_engine import ExecutionEngine
from paml_convert.markdown.markdown_specialization import MarkdownSpecialization
from paml_convert.behavior_specialization import DefaultBehaviorSpecialization
from paml.primitive_execution import initialize_primitive_compute_output


PARAMETER_IN = 'http://bioprotocols.org/uml#in'
PARAMETER_OUT = 'http://bioprotocols.org/uml#out'

paml.import_library('sample_arrays')
paml.import_library('plate_handling')
paml.import_library('spectrophotometry')

class TestProtocolOutputs(unittest.TestCase):

    def setUp(self):
        doc = sbol3.Document()
        protocol = paml.Protocol('foo')
        doc.add(protocol)

        plate_spec = paml.ContainerSpec('my_absorbance_measurement_plate',
                                        name='my absorbance measurement plate',
                                        queryString='cont:Plate96Well',
                                        prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'})
        plate = protocol.primitive_step('EmptyContainer',
                                       specification=plate_spec)
        target_wells = protocol.primitive_step('PlateCoordinates',
                                               source=plate.output_pin('samples'),
                                               coordinates=f'A1')
        measure_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                                     samples=target_wells.output_pin('samples'),
                                                     wavelength=sbol3.Measure(600, tyto.OM.nanometer))

        self.protocol = protocol
        self.output = measure_absorbance.output_pin('measurements')

    #@unittest.expectedFailure
    #def test_protocol_outputs_not_designated(self):
    #    # TODO: catch output parameters that aren't explicitly designated
    #    # rather than breaking cryptically
    #    agent = sbol3.Agent("test_agent")
    #    ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
    #    ex = ee.execute(self.protocol, agent, id="test_execution", parameter_values=[])

    def test_protocol_outputs(self):
        # This test confirms generation of designated output objects
        self.protocol.designate_output('measurements', 'http://bioprotocols.org/paml#SampleData', source=self.output)

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")])
        ex = ee.execute(self.protocol, agent, id="test_execution", parameter_values=[])

        self.assertTrue(isinstance(ex.parameter_values[0].value, uml.LiteralReference))
        self.assertTrue(isinstance(ex.parameter_values[0].value.value.lookup(),
                                   paml.SampleData))


if __name__ == '__main__':
    unittest.main()
