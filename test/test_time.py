import sbol3
import paml
import unittest
import tyto
# from paml_check.paml_check import check_doc, get_minimum_duration


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
        t1 = paml.TimeVariable("t1", value=sbol3.Measure(0, tyto.OM.hour))
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
        a = paml.Join()
        t1a = paml.TimeVariable("t1a",
                                value=sbol3.Measure(0, tyto.OM.hour),
                                time_property=sbol3.provenance.PROV_STARTED_AT_TIME,
                                time_of=a)
        assert t1a.time_property
        t2a = paml.TimeVariable("t2a",
                                value=sbol3.Measure(10, tyto.OM.hour),
                                time_property=sbol3.provenance.PROV_ENDED_AT_TIME,
                                time_of=a)
        assert t2a.time_property

        p = paml.PrimitiveExecutable(instance_of=paml.Primitive("a"))
        t1p = paml.TimeVariable("t1p",
                                value=sbol3.Measure(0, tyto.OM.hour),
                                time_property=sbol3.provenance.PROV_STARTED_AT_TIME,
                                time_of=p)
        assert t1p.time_property
        t2p = paml.TimeVariable("t2p",
                                value=sbol3.Measure(10, tyto.OM.hour),
                                time_property=sbol3.provenance.PROV_ENDED_AT_TIME,
                                time_of=p)
        assert t2p.time_property
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
        protocol = paml.Protocol('test_protocol')
        t1 = paml.EqualsComparison("et1",
                                   term1=paml.TimeVariable("t1",
                                                           time_property=sbol3.provenance.PROV_STARTED_AT_TIME,
                                                           time_of=protocol.initial()),
                                   term2=sbol3.Measure(0, tyto.OM.hour)
                               )

        t2 = paml.EqualsComparison("et2",
                                   term1=paml.TimeVariable("t2",
                                                           time_property=sbol3.provenance.PROV_ENDED_AT_TIME,
                                                           time_of=protocol.final()),
                                   term2=sbol3.Measure(10, tyto.OM.hour)
                               )

        protocol.time_constraints = paml.AndConstraint("ac", clause=[t1, t2])
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
        protocol.add_flow(protocol.initial(), provision_ludox)

        location = paml.ContainerCoordinates(in_container=plate, coordinates='A2:D2')
        protocol.locations.append(location)
        provision_ddh2o = protocol.execute_primitive('Provision', resource=ddh2o, destination=location,
                                                     amount=sbol3.Measure(100, tyto.OM.microliter))
        protocol.add_flow(protocol.initial(), provision_ddh2o)

        all_provisioned = paml.Join()
        protocol.activities.append(all_provisioned)
        protocol.add_flow(provision_ludox.output_pin('samples'), all_provisioned)
        protocol.add_flow(provision_ddh2o.output_pin('samples'), all_provisioned)

        execute_measurement = protocol.execute_primitive('MeasureAbsorbance', samples=all_provisioned,
                                                         wavelength=sbol3.Measure(600, tyto.OM.nanometer))

        result = protocol.add_output('absorbance', execute_measurement.output_pin('measurements'))
        protocol.add_flow(result, protocol.final())

        # Set protocol timepoints
        start = paml.TimeVariable("start_time",
                                    time_of=protocol.initial(),
                                    time_property=sbol3.provenance.PROV_STARTED_AT_TIME)
        ce1 = paml.ConstantExpression("ce1", term=sbol3.Measure(0.0, tyto.OM.hour))
        protocol_start_time = paml.EqualsComparison(
            "protocol_start_time_equals",
            term1=start,
            term2=ce1)

        provision_ludox_duration = \
            paml.Duration("provision_ludox_duration",
                          time_of=provision_ludox,
                          value=sbol3.Measure(60, tyto.OM.second))

        provision_ddh2o_duration = \
            paml.Duration("provision_ddh2o_duration",
                          time_of=provision_ddh2o,
                          value=sbol3.Measure(60, tyto.OM.second))

        execute_measurement_duration = \
            paml.Duration("execute_measurement_duration",
                          time_of=execute_measurement,
                          value=sbol3.Measure(600, tyto.OM.second))

        ludox_end = paml.TimeVariable("ludox_end",
                                    time_of=provision_ludox,
                                    time_property=sbol3.provenance.PROV_ENDED_AT_TIME)
        ddh2o_start = paml.TimeVariable("ddh2o_start",
                                    time_of=provision_ddh2o,
                                    time_property=sbol3.provenance.PROV_STARTED_AT_TIME)

        ludox_before_ddh2o_constraint = paml.LessThanEqualComparison(
            "ludox_before_ddh2o",
            term1=ludox_end,
            term2=ddh2o_start)

        timepoints = [
            ludox_end,
            ddh2o_start,
            start,
            ce1
        ]
        clauses = [ protocol_start_time,
                    provision_ludox_duration,
                    provision_ddh2o_duration,
                    execute_measurement_duration,
                    ludox_before_ddh2o_constraint ]
        time_constraints = paml.AndConstraint("tcs", clause=clauses)

        doc.add(time_constraints)
        for t in timepoints:
            doc.add(t)
        protocol.time_constraints = time_constraints

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # assert check_doc(doc) # Is the protocol consistent?

        # assert get_minimum_duration(doc)  # What is the minimum duration for each protocol in doc
        doc.write('igem_ludox_time_draft.ttl', 'turtle')

        assert doc


    def test_expressions(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Expressions
        print('Creating Protocol')
        t1 = paml.TimeVariable("t1")
        e1 = paml.VariableExpression("e1", term=t1)

        a1 = paml.Join()
        d1 = paml.Duration("d1", time_of=a1)
        e2 = paml.VariableExpression("e2", term=d1)

        m1 = sbol3.Measure(60, tyto.OM.second)
        e3 = paml.ConstantExpression("e3", term=m1)

        e4 = paml.ProductExpression("e4", term1=e3, term2=e2)

        expressions = [e1, e2, e3, e4]

        for e in expressions:
            doc.add(e)

        lt1 = paml.LessThanComparison("lt1", term1=e4, term2=e2)

        c1 = paml.NotConstraint("c1", clause=lt1)

        constraints = [lt1, c1]

        for c in constraints:
            doc.add(c)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')

if __name__ == '__main__':
    unittest.main()
