import sbol3
import paml
import unittest
import tyto

class TestTime(unittest.TestCase):
    def test_difference(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Difference
        print('Creating Difference')
        t1 = paml.TimeVariable("t1", value=sbol3.Measure(0, tyto.OM.time))
        t2 = paml.TimeVariable("t2")
        d1 = paml.Difference("d1", source=t1, destination=t2)
        doc.add(d1)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('difference.nt', 'sorted nt')
        # doc.write('difference.ttl', 'turtle')

    def test_timed_activity(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Activity
        print('Creating Activity')
        t1a = paml.TimeVariable("t1a", value=sbol3.Measure(0, tyto.OM.time))
        t2a = paml.TimeVariable("t2a")
        d1a = paml.TimeVariable("d1a")
        a = paml.Join(start=t1a, end=t2a, duration=d1a)
        t1p = paml.TimeVariable("t1p", value=sbol3.Measure(0, tyto.OM.time))
        t2p = paml.TimeVariable("t2p")
        d1p = paml.TimeVariable("d1p")
        p = paml.Primitive("p", start=t1p, end=t2p, duration=d1p)
        #doc.add(a)
        doc.add(p)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')

    def test_timed_protocol(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Protocol
        print('Creating Protocol')
        t1 = paml.TimeVariable("t1", value=sbol3.Measure(0, tyto.OM.time))
        t2 = paml.TimeVariable("t2")
        d1 = paml.TimeVariable("d1")
        protocol = paml.Protocol('test_protocol', start=t1, end=t2, duration=d1)
        doc.add(protocol)


        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')


if __name__ == '__main__':
    unittest.main()
