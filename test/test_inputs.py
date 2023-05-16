import unittest

import sbol3
import tyto

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert import MarkdownSpecialization
from labop_convert.behavior_specialization import DefaultBehaviorSpecialization

PARAMETER_IN = "http://bioprotocols.org/uml#in"
PARAMETER_OUT = "http://bioprotocols.org/uml#out"

labop.import_library("sample_arrays")
labop.import_library("liquid_handling")


class TestProtocolInputs(unittest.TestCase):
    def test_input_object_not_contained_in_document(self):
        # Automatically add input objects to a Document #157
        protocol, doc = labop.Protocol.initialize_protocol()

        # Create the input, but don't add it to the Document yet
        input = sbol3.Component("input", sbol3.SBO_DNA)

        container = protocol.primitive_step(
            "EmptyContainer",
            specification=labop.ContainerSpec(
                "empty_container",
                name=f"empty container",
                queryString="cont:Plate96Well",
                prefixMap={
                    "cont": "https://sift.net/container-ontology/container-ontology#"
                },
            ),
        )

        provision = protocol.primitive_step(
            "Provision",
            resource=input,
            destination=container.output_pin("samples"),
            amount=sbol3.Measure(0, None),
        )

        assert input in doc.objects

    def test_unbounded_inputs(self):
        protocol, doc = labop.Protocol.initialize_protocol()

        p = labop.Primitive("ContainerSet")
        p.add_input("inputs", sbol3.SBOL_COMPONENT, unbounded=True)
        self.assertIsNone(p.parameters[0].property_value.upper_value)
        doc.add(p)

        input1 = sbol3.Component("input1", sbol3.SBO_DNA, name="input1")
        input2 = sbol3.Component("input2", sbol3.SBO_DNA, name="input2")
        doc.add(input1)
        doc.add(input2)

        container_set = protocol.primitive_step(p, inputs=[input1, input2])
        self.assertEqual(len(container_set.input_pins("inputs")), 2)
        # assert(len([p for p in container_set.inputs if p.name=='sources']) == 2)

        def container_set_execution(record):
            call = record.call.lookup()
            parameter_value_map = call.parameter_value_map()
            sources = parameter_value_map["sources"]
            container = parameter_value_map["specification"]
            samples = parameter_value_map["samples"]

        ee = ExecutionEngine()
        ee.specializations[0]._behavior_func_map[p.identity] = lambda record, ex: None
        ex = ee.execute(
            protocol,
            sbol3.Agent("test_agent"),
            id="test_execution1",
            parameter_values=[],
        )

        # Check that execution has correct inputs
        [container_execution] = [
            x for x in ex.executions if x.node == container_set.identity
        ]
        call = container_execution.call.lookup()
        self.assertEqual(len(call.parameter_value_map()["inputs"]), 2)


if __name__ == "__main__":
    unittest.main()
