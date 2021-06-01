import sbol3
import paml
import unittest
import tyto
from paml_check.paml_check import check_doc

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
        t1 = paml.TimeVariable(value=sbol3.Measure(0, tyto.OM.time))
        t2 = paml.TimeVariable()
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
        t1a = paml.TimeVariable(value=sbol3.Measure(0, tyto.OM.time))
        t2a = paml.TimeVariable()
        d1a = paml.TimeVariable()
        a = paml.Join(start=t1a, end=t2a, duration=d1a)
        t1p = paml.TimeVariable(value=sbol3.Measure(0, tyto.OM.time))
        t2p = paml.TimeVariable()
        d1p = paml.TimeVariable()
        p = paml.PrimitiveExecutable(start=t1p, end=t2p, duration=d1p)
        #doc.add(a)
        #doc.add(p)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')

    def test_timed_small_protocol(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Protocol
        print('Creating Protocol')
        t1 = paml.TimeVariable(value=sbol3.Measure(0, tyto.OM.time))
        t2 = paml.TimeVariable()
        d1 = paml.TimeVariable()
        protocol = paml.Protocol('test_protocol', start=t1, end=t2, duration=d1)
        doc.add(protocol)


        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')

    def test_create_timed_protocol(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')

        #############################################
        # Import the primitive libraries
        print('Importing libraries')
        paml.import_library('liquid_handling')
        paml.import_library('plate_handling')
        paml.import_library('spectrophotometry')

        #############################################
        # Create the protocol
        print('Creating protocol')
        protocol = paml.Protocol('iGEM_LUDOX_OD_calibration_2018')
        protocol.name = "iGEM 2018 LUDOX OD calibration protocol"
        protocol.description = '''
With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
        '''
        doc.add(protocol)

        # Set protocol timepoints
        protocol.initialize_timepoints()
        protocol.start.value = sbol3.Measure(0, tyto.OM.time)

        # create the materials to be provisioned
        plate = paml.Container(name='Microplate', type=tyto.NCIT.get_uri_by_term('Microplate'), max_coordinate='H12')
        protocol.locations.append(plate)

        ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
        ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # TODO get via tyto
        doc.add(ddh2o)

        ludox = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
        ludox.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
        doc.add(ludox)

        protocol.material += {ddh2o, ludox}

        # actual steps of the protocol
        location = paml.ContainerCoordinates(in_container=plate, coordinates='A1:D1')
        protocol.locations.append(location)
        provision_ludox = protocol.execute_primitive('Provision', resource=ludox, destination=location,
                                                     amount=sbol3.Measure(100, tyto.OM.microliter))
        provision_ludox.duration.value = sbol3.Measure(10, tyto.OM.time)
        protocol.add_flow(protocol.initial(), provision_ludox)

        location = paml.ContainerCoordinates(in_container=plate, coordinates='A2:D2')
        protocol.locations.append(location)
        provision_ddh2o = protocol.execute_primitive('Provision', resource=ddh2o, destination=location,
                                                     amount=sbol3.Measure(100, tyto.OM.microliter))
        provision_ddh2o.duration.value = sbol3.Measure(10, tyto.OM.time)
        protocol.add_flow(protocol.initial(), provision_ddh2o)

        all_provisioned = paml.control_initialize_timepoints(paml.Join())
        protocol.activities.append(all_provisioned)
        protocol.add_flow(provision_ludox.output_pin('samples'), all_provisioned)
        protocol.add_flow(provision_ddh2o.output_pin('samples'), all_provisioned)

        execute_measurement = protocol.execute_primitive('MeasureAbsorbance', samples=all_provisioned,
                                                         wavelength=sbol3.Measure(600, tyto.OM.nanometer))
        execute_measurement.duration.value = sbol3.Measure(100, tyto.OM.time)
        result = protocol.add_output('absorbance', execute_measurement.output_pin('measurements'))
        protocol.add_flow(result, protocol.final())

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        doc_result = check_doc(doc)
        assert doc_result

if __name__ == '__main__':
    unittest.main()
