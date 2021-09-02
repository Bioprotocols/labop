import unittest
import sbol3
import paml
import uml


class TestValidationErrorChecking(unittest.TestCase):
    def test_activity_multiflow(self):
        """Test whether validator can detect nondeterminism due to activity multiple outflows"""
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

    def test_activity_bad_inflows(self):
        """Test whether validator can detect error due to excess or missing inflows"""
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')
        # Create the protocol
        print('Creating protocol')
        protocol = paml.Protocol('broken')
        doc.add(protocol)
        # call order backwards, to make an edge from the final to the initial
        protocol.order(protocol.final(), protocol.initial())
        # access a parameter node and order it backwards too
        p = uml.ActivityParameterNode()
        protocol.nodes.append(p)
        protocol.order(protocol.final(), p)
        # Validate the document, which should produce two errors
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 3, f'Expected 3 validation issues, but found {len(v)}'
        expected = [
            'https://bbn.com/scratch/broken/ActivityParameterNode1: Too few values for property parameter. Expected 1, found 0',
            'https://bbn.com/scratch/broken/InitialNode1: InitialNode must have no incoming edges, but has 1',
            'https://bbn.com/scratch/broken/FlowFinalNode1: Node has no incoming edges, so cannot be executed'
            ]
        observed = [str(e) for e in v]
        assert observed == expected, f'Unexpected error content: {observed}'

if __name__ == '__main__':
    unittest.main()
