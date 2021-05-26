import sbol3
import paml
import unittest


class TestTime(unittest.TestCase):
    def test_create_time(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the time
        print('Creating time')
        tp1 = paml.Difference("a", source=None)
        doc.add(tp1)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        doc.write('time_test.nt', 'sorted nt')
        doc.write('time_test.ttl', 'turtle')


if __name__ == '__main__':
    unittest.main()
