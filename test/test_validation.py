import unittest
import sbol3
import paml
import uml


class TestValidationErrorChecking(unittest.TestCase):
    def test_activity_multiflow(self):
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')
        paml.import_library('sample_arrays')
        # Create the protocol
        print('Creating protocol')
        protocol = paml.Protocol('broken')
        doc.add(protocol)
        # get a plate
        plate = protocol.primitive_step('EmptyContainer', specification='placeholder')
        # use it in three places
        s1 = protocol.primitive_step('PlateCoordinates', coordinates='A1:D1')
        protocol.edges.append(uml.ObjectFlow(source=plate.output_pin('samples'),target=s1.input_pin('source')))
        s2 = protocol.primitive_step('PlateCoordinates', coordinates='A2:D2')
        protocol.edges.append(uml.ObjectFlow(source=plate.output_pin('samples'),target=s2.input_pin('source')))
        s3 = protocol.primitive_step('PlateCoordinates', coordinates='A3:D3')
        protocol.edges.append(uml.ObjectFlow(source=plate.output_pin('samples'),target=s3.input_pin('source')))
        # Validate the document, which should produce one error
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v.errors) == 0, f'Expected zero errors, but found {len(v)}'
        assert len(v.warnings) == 1, f'Expected precisely one warning, but found {len(v)}'
        assert str(v.warnings[0]) == \
               'https://bbn.com/scratch/broken/CallBehaviorAction1/OutputPin1: ' \
               'ActivityNode has 3 outgoing edges: multi-edges can cause nondeterministic flow', \
                f'Unexpected warning content: {str(v.warnings[0])}'



if __name__ == '__main__':
    unittest.main()
