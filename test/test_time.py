import filecmp
import os
import tempfile

import sbol3
import unittest
import tyto
import paml_time as pamlt
import paml
import uml
# from paml_check.paml_check import check_doc, get_minimum_duration


class TestTime(unittest.TestCase):
    def test_single_behavior(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the behavior and constraints
        print('Creating Constraints')

        a = paml.Primitive("a")
        # Constrain start time of a to [0, 10]
        start_a = pamlt.startTime(a, [0, 10], units=tyto.OM.hour)

        # Constrain end time of a to [10, 15]
        end_a = pamlt.endTime(a, [10, 15], units=tyto.OM.hour)

        # Constrain duration of a to [1, 5]
        duration_a = pamlt.duration(a, [1, 5], units=tyto.OM.hour)

        constraint = pamlt.And([start_a, end_a, duration_a])
        time_constraints = pamlt.TimeConstraints("small_protocol_constraints", constraints=[constraint])


        doc.add(a)
        doc.add(time_constraints)
        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('difference.nt', 'sorted nt')
        # doc.write('difference.ttl', 'turtle')

    def test_two_behaviors(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the behavior and constraints
        print('Creating Constraints')

        a = paml.Primitive("a")
        b = paml.Primitive("b")

        # Constrain start of b to follow end of a by [10, 15]
        follows_constraint = pamlt.precedes(a, [10, 15], b, units=tyto.OM.hour)

        doc.add(a)
        # doc.add(follows_constraint)
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

        # Protocol starts at time zero
        start = pamlt.startTime(protocol, 0, units=tyto.OM.hour)

        # Protocol lasts 10 - 15 hours
        duration = pamlt.duration(protocol, [10, 15], units=tyto.OM.hour)

        time_constraints = pamlt.TimeConstraints("small_protocol_constraints",
                                                 constraints=pamlt.And([start, duration]),
                                                 protocols=[protocol])
        doc.add(protocol)
        doc.add(time_constraints)


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
        print('... Imported liquid handling')
        paml.import_library('plate_handling')
        print('... Imported plate handling')
        paml.import_library('spectrophotometry')
        print('... Imported spectrophotometry')
        paml.import_library('sample_arrays')
        print('... Imported sample arrays')

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
        ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
        ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # TODO get via tyto
        doc.add(ddh2o)

        ludox = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
        ludox.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
        doc.add(ludox)

        # actual steps of the protocol
        # get a plate
        plate = protocol.primitive_step('EmptyContainer', specification=tyto.NCIT.get_uri_by_term('Microplate'))  # replace with container ontology

        # put ludox and water in selected wells
        c_ddh2o = protocol.primitive_step('PlateCoordinates', source=plate, coordinates='A1:D1')
        provision_ludox = protocol.primitive_step('Provision', resource=ludox, destination=c_ddh2o.output_pin('samples'),
                                                  amount=sbol3.Measure(100, tyto.OM.microliter))

        c_ludox = protocol.primitive_step('PlateCoordinates', source=plate, coordinates='A2:D2')
        provision_ddh2o = protocol.primitive_step('Provision', resource=ddh2o, destination=c_ludox.output_pin('samples'),
                                                  amount=sbol3.Measure(100, tyto.OM.microliter))

        # measure the absorbance
        c_measure = protocol.primitive_step('PlateCoordinates', source=plate, coordinates='A1:D2')
        measure = protocol.primitive_step('MeasureAbsorbance', samples=c_measure,
                                          wavelength=sbol3.Measure(600, tyto.OM.nanometer))

        protocol.add_output('absorbance', measure.output_pin('measurements'))

        # Set protocol timepoints

        # protocol starts at time 0
        protocol_start_time = pamlt.startTime(protocol, 0, units=tyto.OM.hour)
        provision_ludox_duration = pamlt.duration(provision_ludox, 60, units=tyto.OM.second)
        provision_ddh2o_duration = pamlt.duration(provision_ddh2o, 60, units=tyto.OM.second)
        execute_measurement_duration = pamlt.duration(measure, 60, units=tyto.OM.minute)
        ludox_before_ddh2o_constraint = pamlt.precedes(provision_ludox, [10, 15], provision_ddh2o, units=tyto.OM.hour)

        time_constraints = pamlt.TimeConstraints("ludox_protocol_constraints",
            constraints=[pamlt.And([
                protocol_start_time,
                provision_ludox_duration,
                provision_ddh2o_duration,
                execute_measurement_duration,
                ludox_before_ddh2o_constraint
                ])],
            protocols = [protocol]
        )

        doc.add(time_constraints)

        ########################################
        # Validate and write the document
        print('Validating and writing protocol')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # assert check_doc(doc) # Is the protocol consistent?
        # assert get_minimum_duration(doc)  # What is the minimum duration for each protocol in doc

        temp_name = os.path.join(tempfile.gettempdir(), 'igem_ludox_time_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'igem_ludox_time_test.nt')
        doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


    def test_expressions(self):
        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')


        #############################################
        # Create the Expressions
        print('Creating Protocol')

        # expression e1: 60s * duration(a1)
        a1 = paml.Primitive("a1")
        d1 = uml.Duration(observation=uml.DurationObservation(event=[a1]))
        m1 = pamlt.TimeMeasure(expr=sbol3.Measure(60, tyto.OM.second))
        e1 = uml.Expression(symbol="*", is_ordered=False, operand=[m1, d1])
        #doc.add(e1)


        # expression lt1: e1 < e2
        e2 = pamlt.TimeMeasure(expr=sbol3.Measure(120, tyto.OM.second))
        lt1 = uml.Expression(symbol="<", is_ordered=True, operand=[e1, e2])
        #doc.add(lt1)

        # c1: Not(lt1)
        c1 = pamlt.Not(constrained_elements=lt1)
        #  doc.add(c1)

        ########################################
        # Validate and write the document
        print('Validating and writing time')
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(str(e) for e in doc.validate().errors)

        # doc.write('timed_protocol.nt', 'sorted nt')
        # doc.write('timed_protocol.ttl', 'turtle')

if __name__ == '__main__':
    unittest.main()
