import tempfile
import os
import unittest
import filecmp
import sbol3
import paml


class TestLibraryBuilding(unittest.TestCase):
    def test_two_element_library(self):
        #############################################
        # Set up the document
        doc = sbol3.Document()
        sbol3.set_namespace('https://example.org/test')

        #############################################
        # Create the primitives
        print('Making primitives for test library')

        p = paml.Primitive('Provision')
        p.description = 'Place a measured amount (mass or volume) of a specified component into a location.'
        p.add_input('resource', sbol3.SBOL_COMPONENT)
        p.add_input('destination', 'http://bioprotocols.org/paml#Location')
        p.add_input('amount', sbol3.OM_MEASURE)  # Can be mass or volume
        p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
        p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
        doc.add(p)

        p = paml.Primitive('Transfer')
        p.description = 'Move a measured volume taken from a collection of source samples to a location'
        p.add_input('source', 'http://bioprotocols.org/paml#LocatedSamples')
        p.add_input('destination', 'http://bioprotocols.org/paml#Location')
        p.add_input('amount', sbol3.OM_MEASURE)  # Must be volume
        p.add_input('dispenseVelocity', sbol3.OM_MEASURE, True)
        p.add_output('samples', 'http://bioprotocols.org/paml#LocatedSamples')
        doc.add(p)

        print('Library construction complete')

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), 'mini_library.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'mini_library.nt')
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
