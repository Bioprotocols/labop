import unittest
import os
import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization
from labop_convert.behavior_specialization import DefaultBehaviorSpecialization
import sbol3


PARAMETER_IN = "http://bioprotocols.org/uml#in"
PARAMETER_OUT = "http://bioprotocols.org/uml#out"


OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)


class ExampleProtocol(unittest.TestCase):
    def test_bottom_up_protocol(self):
        # Provides a minimal, working example of a Protocol built from
        # the bottom-up without using any of the library's convenience methods
        doc = sbol3.Document()
        protocol = labop.Protocol("foo")
        doc.add(protocol)

        step1 = labop.Primitive("step1")
        step2 = labop.Primitive("step2")

        step1_output = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step2_input = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_IN,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1.parameters.append(step1_output)
        step2.parameters.append(step2_input)

        doc.add(step1)
        doc.add(step2)

        start_action = uml.InitialNode()
        step1_action = uml.CallBehaviorAction(behavior=step1)
        step2_action = uml.CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(uml.ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(uml.ControlFlow(source=step1_action, target=step2_action))

        output = uml.OutputPin(name="samples", is_ordered=True, is_unique=True)
        step1_action.outputs.append(output)

        input = uml.InputPin(name="samples", is_ordered=True, is_unique=True)
        step2_action.inputs.append(input)
        flow = uml.ObjectFlow(source=output, target=input)
        protocol.edges.append(flow)

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(out_dir=OUT_DIR)

        ee.specializations[0]._behavior_func_map[
            step1.identity
        ] = lambda record, ex: None
        ee.specializations[0]._behavior_func_map[
            step2.identity
        ] = lambda record, ex: None

        # execute protocol
        x = ee.execute(protocol, agent, id="test_execution", parameter_values=[])


class TestParameters(unittest.TestCase):
    def test_parameters_not_found(self):
        # Verify exception-handling when user specifies a Pin that doesn't match expected Parameter names
        doc = sbol3.Document()
        protocol = labop.Protocol("foo")
        doc.add(protocol)

        step1 = labop.Primitive("step1")
        step2 = labop.Primitive("step2")
        step1_output = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step2_input = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_IN,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1.parameters.append(step1_output)
        step2.parameters.append(step2_input)

        doc.add(step1)
        doc.add(step2)

        start_action = uml.InitialNode()
        step1_action = uml.CallBehaviorAction(behavior=step1)
        step2_action = uml.CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(uml.ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(uml.ControlFlow(source=step1_action, target=step2_action))

        # Action pin "output" does not match expected Primitive Parameters
        step1_action.outputs.append(
            uml.OutputPin(name="output", is_ordered=True, is_unique=True)
        )
        step2_action.inputs.append(
            uml.InputPin(name="input", is_ordered=True, is_unique=True)
        )

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            out_dir=OUT_DIR,
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")],
        )
        parameter_values = []

        with self.assertRaises(ValueError):
            x = ee.execute(
                protocol, agent, id="test_execution", parameter_values=parameter_values
            )

    def test_duplicate_parameters(self):
        # Verify exception-handling for name collisions between Parameters
        doc = sbol3.Document()
        protocol = labop.Protocol("foo")
        doc.add(protocol)

        step1 = labop.Primitive("step1")
        step2 = labop.Primitive("step2")

        # create duplicate Parameters for the step1 Primitive, resulting in a failure mode
        step1_output = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1_duplicate_output = uml.OrderedPropertyValue(
            index=2,
            property_value=uml.Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )

        step1.parameters.append(step1_output)
        step1.parameters.append(step1_duplicate_output)
        doc.add(step1)
        doc.add(step2)

        start_action = uml.InitialNode()
        step1_action = uml.CallBehaviorAction(behavior=step1)
        step2_action = uml.CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(uml.ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(uml.ControlFlow(source=step1_action, target=step2_action))

        step1_action.outputs.append(
            uml.OutputPin(name="samples", is_ordered=True, is_unique=True)
        )
        step1_action.outputs.append(
            uml.OutputPin(name="samples", is_ordered=True, is_unique=True)
        )

        ## Need to define an output for the "samples" output, otherwise ee will compute unique values for each: "samples0", "samples1", etc.
        def step1_compute_output(inputs, parameter, sample_format):
            return "samples_value"

        step1.compute_output = step1_compute_output

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")]
        )
        parameter_values = []
        with self.assertRaises(ValueError):
            x = ee.execute(
                protocol, agent, id="test_execution", parameter_values=parameter_values
            )

    def test_optional_and_required_parameters(self):
        doc = sbol3.Document()
        protocol = labop.Protocol("foo")
        doc.add(protocol)

        input_component = sbol3.Component("input_component", sbol3.SBO_DNA)
        doc.add(input_component)

        step1 = labop.Primitive("step1")

        # create optional parameter
        step1_optional_input1 = uml.OrderedPropertyValue(
            index=1,
            property_value=uml.Parameter(
                name="step1_optional_input1",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_IN,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1_optional_input1.property_value.lower_value = uml.LiteralInteger(value=0)
        step1_optional_input2 = uml.OrderedPropertyValue(
            index=2,
            property_value=uml.Parameter(
                name="step1_optional_input2",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_IN,
                is_ordered=True,
                is_unique=True,
            ),
        )  # Omit the lower value. This formerly caused an exception. See #119

        step1.parameters.append(step1_optional_input1)
        step1.parameters.append(step1_optional_input2)
        doc.add(step1)

        start_action = uml.InitialNode()
        step1_action = uml.CallBehaviorAction(behavior=step1)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.edges.append(uml.ControlFlow(source=start_action, target=step1_action))

        # Execute without specifying InputPins, this should work fine, since the Parameters are optional
        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(out_dir=OUT_DIR)
        ee.specializations[0]._behavior_func_map[
            step1.identity
        ] = (
            lambda record, ex: None
        )  # Register custom primitives in the execution engine

        x = ee.execute(protocol, agent, id="test_execution1", parameter_values=[])

        # Make optional input required, and re-execute, triggering an exception, because
        # no input pin is provided
        step1_optional_input1.property_value.lower_value = uml.LiteralInteger(value=1)
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution2", parameter_values=[])

        # Now provide the required input pin, but it is missing its value. See #130
        step1_action.inputs.append(
            uml.ValuePin(name="step1_optional_input1", is_ordered=True, is_unique=True)
        )
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution3", parameter_values=[])

        # Provide the remaining, optional Pin. This too should fail because it does not have
        # a ValueSpecification
        step1_action.inputs.append(
            uml.ValuePin(name="step1_optional_input2", is_ordered=True, is_unique=True)
        )
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution4", parameter_values=[])

        # Now that Pins have a valid ValueSpecification, we should be able to execute
        # successfully
        step1_action.inputs[0].value = uml.LiteralReference(value=input_component)
        step1_action.inputs[1].value = uml.LiteralReference(value=input_component)
        x = ee.execute(protocol, agent, id="test_execution5", parameter_values=[])

    def test_bad_ordered_property_value(self):
        # Tests what happens when OrderedPropertyValue indexes are not
        # sequentially ordered
        pass

    def test_output_tokens(self):
        # Tests that the correct output objects are generated from
        # a CallBehaviorExecution.  This should exercise the
        # different cases in BehaviorExecution.parameter_value_map and
        # Primitive.compute_output.  It should also test the failure
        # case when a Primitive's output Parameter has an unrecognized type
        pass


if __name__ == "__main__":
    unittest.main()
