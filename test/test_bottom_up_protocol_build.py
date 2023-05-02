import os
import unittest

import sbol3
from numpy import source

from labop import (
    CallBehaviorAction,
    ControlFlow,
    ExecutionEngine,
    InitialNode,
    Primitive,
    Protocol,
)
from labop_convert import MarkdownSpecialization
from labop_convert.behavior_specialization import DefaultBehaviorSpecialization
from uml import (
    InputPin,
    LiteralInteger,
    LiteralReference,
    ObjectFlow,
    OutputPin,
    ValuePin,
)
from uml.final_node import FinalNode
from uml.ordered_property_value import OrderedPropertyValue
from uml.parameter import Parameter

PARAMETER_IN = "http://bioprotocols.org/uml#in"
PARAMETER_OUT = "http://bioprotocols.org/uml#out"


OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)


class ExampleProtocol(unittest.TestCase):
    def test_bottom_up_protocol(self):
        # Provides a minimal, working example of a Protocol built from
        # the bottom-up without using any of the library's convenience methods
        protocol, doc = Protocol.initialize_protocol(display_id="foo")

        step1 = Primitive("step1")
        step2 = Primitive("step2")

        step1_output = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step2_input = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
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

        start_action = InitialNode()
        step1_action = CallBehaviorAction(behavior=step1)
        step2_action = CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(ControlFlow(source=step1_action, target=step2_action))

        output = OutputPin(name="samples", is_ordered=True, is_unique=True)
        step1_action.get_outputs().append(output)

        input = InputPin(name="samples", is_ordered=True, is_unique=True)
        step2_action.get_inputs().append(input)
        flow = ObjectFlow(source=output, target=input)
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
        protocol = Protocol("foo")
        doc.add(protocol)

        step1 = Primitive("step1")
        step2 = Primitive("step2")
        step1_output = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step2_input = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
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

        start_action = InitialNode()
        step1_action = CallBehaviorAction(behavior=step1)
        step2_action = CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(ControlFlow(source=step1_action, target=step2_action))

        # Action pin "output" does not match expected Primitive Parameters
        step1_action.get_outputs().append(
            OutputPin(name="output", is_ordered=True, is_unique=True)
        )
        step2_action.get_inputs().append(
            InputPin(name="input", is_ordered=True, is_unique=True)
        )

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            out_dir=OUT_DIR,
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")],
        )
        parameter_values = []

        with self.assertRaises(ValueError):
            x = ee.execute(
                protocol,
                agent,
                id="test_execution",
                parameter_values=parameter_values,
            )

    def test_duplicate_parameters(self):
        # Verify exception-handling for name collisions between Parameters

        protocol, doc = Protocol.initialize_protocol(display_id="foo")
        step1 = Primitive("step1")
        step2 = Primitive("step2")

        # create duplicate Parameters for the step1 Primitive, resulting in a failure mode
        step1_output = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
                name="samples",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_OUT,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1_duplicate_output = OrderedPropertyValue(
            index=2,
            property_value=Parameter(
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

        start_action = InitialNode()
        step1_action = CallBehaviorAction(behavior=step1)
        step2_action = CallBehaviorAction(behavior=step2)
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.nodes.append(step2_action)
        protocol.edges.append(ControlFlow(source=start_action, target=step1_action))
        protocol.edges.append(ControlFlow(source=step1_action, target=step2_action))

        op1 = OutputPin(name="samples", is_ordered=True, is_unique=True)
        step1_action.get_outputs().append(op1)
        protocol.edges.append(ObjectFlow(source=step1_action, target=op1))

        op2 = OutputPin(name="samples", is_ordered=True, is_unique=True)
        step1_action.get_outputs().append(
            OutputPin(name="samples", is_ordered=True, is_unique=True)
        )
        protocol.edges.append(ObjectFlow(source=step1_action, target=op2))

        ## Need to define an output for the "samples" output, otherwise ee will compute unique values for each: "samples0", "samples1", etc.
        def step1_compute_output(inputs, parameter, sample_format, record_hash):
            return "samples_value"

        step1.compute_output = step1_compute_output

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")]
        )
        parameter_values = []
        with self.assertRaises(ValueError):
            x = ee.execute(
                protocol,
                agent,
                id="test_execution",
                parameter_values=parameter_values,
            )

    def test_optional_and_required_parameters(self):
        protocol, doc = Protocol.initialize_protocol(display_id="foo")

        input_component = sbol3.Component("input_component", sbol3.SBO_DNA)
        doc.add(input_component)

        step1 = Primitive("step1")

        # create optional parameter
        step1_optional_input1 = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
                name="step1_optional_input1",
                type=sbol3.SBOL_COMPONENT,
                direction=PARAMETER_IN,
                is_ordered=True,
                is_unique=True,
            ),
        )
        step1_optional_input1.property_value.lower_value = LiteralInteger(value=0)
        step1_optional_input2 = OrderedPropertyValue(
            index=2,
            property_value=Parameter(
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

        start_action = InitialNode()
        step1_action = CallBehaviorAction(behavior=step1)
        final_node = FinalNode()
        protocol.nodes.append(start_action)
        protocol.nodes.append(step1_action)
        protocol.edges.append(ControlFlow(source=start_action, target=step1_action))
        protocol.nodes.append(final_node)
        protocol.edges.append(ControlFlow(source=step1_action, target=final_node))

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
        step1_optional_input1.property_value.lower_value = LiteralInteger(value=1)
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution2", parameter_values=[])

        # Now provide the required input pin, but it is missing its value. See #130
        step1_action.get_inputs().append(
            ValuePin(name="step1_optional_input1", is_ordered=True, is_unique=True)
        )
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution3", parameter_values=[])

        # Provide the remaining, optional Pin. This too should fail because it does not have
        # a ValueSpecification
        step1_action.get_inputs().append(
            ValuePin(name="step1_optional_input2", is_ordered=True, is_unique=True)
        )
        with self.assertRaises(ValueError):
            x = ee.execute(protocol, agent, id="test_execution4", parameter_values=[])

        # Now that Pins have a valid ValueSpecification, we should be able to execute
        # successfully
        step1_action.get_inputs()[0].value = LiteralReference(value=input_component)
        step1_action.get_inputs()[1].value = LiteralReference(value=input_component)
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
