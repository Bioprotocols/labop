import os
import unittest

import sbol3
import tyto

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert import MarkdownSpecialization
from labop_convert.behavior_specialization import DefaultBehaviorSpecialization

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

PARAMETER_IN = "http://bioprotocols.org/uml#in"
PARAMETER_OUT = "http://bioprotocols.org/uml#out"

labop.import_library("sample_arrays")
labop.import_library("plate_handling")
labop.import_library("spectrophotometry")


class TestProtocolOutputs(unittest.TestCase):
    def setUp(self):
        doc = sbol3.Document()
        protocol = labop.Protocol("foo")
        doc.add(protocol)

        plate = protocol.primitive_step(
            "EmptyContainer",
            specification=labop.ContainerSpec(
                "container",
                name=f"my absorbance measurement plate",
                queryString="cont:Plate96Well",
                prefixMap={
                    "cont": "https://sift.net/container-ontology/container-ontology#"
                },
            ),
        )
        target_wells = protocol.primitive_step(
            "PlateCoordinates",
            source=plate.output_pin("samples"),
            coordinates=f"A1",
        )
        measure_absorbance = protocol.primitive_step(
            "MeasureAbsorbance",
            samples=target_wells.output_pin("samples"),
            wavelength=sbol3.Measure(600, tyto.OM.nanometer),
        )

        self.protocol = protocol
        self.output = measure_absorbance.output_pin("measurements")

    def test_protocol_outputs_not_designated(self):
        # TODO: catch output parameters that aren't explicitly designated
        # rather than breaking cryptically
        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            out_dir=OUT_DIR,
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")],
        )
        ex = ee.execute(self.protocol, agent, id="test_execution", parameter_values=[])

    def test_specialized_compute_output(self):
        # This test confirms generation of an output token from a Primitive
        # with a specialized compute_output method
        self.protocol.designate_output(
            "measurements",
            "http://bioprotocols.org/labop#SampleData",
            source=self.output,
        )

        agent = sbol3.Agent("test_agent")
        ee = ExecutionEngine(
            out_dir=OUT_DIR,
            specializations=[MarkdownSpecialization("test_LUDOX_markdown.md")],
        )
        ex = ee.execute(self.protocol, agent, id="test_execution", parameter_values=[])

        self.assertTrue(isinstance(ex.parameter_values[0].value, uml.LiteralReference))
        self.assertTrue(
            isinstance(ex.parameter_values[0].value.value.lookup(), labop.Dataset)
        )

    def test_default_compute_output(self):
        # This test confirms generation of an output token using the default
        # compute_output method

        p = labop.Primitive("Foo")
        p.add_output("output", sbol3.SBOL_COMPONENT)
        self.protocol.document.add(p)

        p_step = self.protocol.primitive_step(p)
        self.protocol.designate_output(
            "protocol output",
            sbol3.SBOL_COMPONENT,
            source=p_step.output_pin("output"),
        )
        self.protocol.designate_output(
            "measurements",
            "http://bioprotocols.org/labop#SampleData",
            source=self.output,
        )

        ee = ExecutionEngine(out_dir=OUT_DIR, failsafe=False)
        ee.specializations[0]._behavior_func_map[
            p.identity
        ] = lambda record, execution: None
        ex = ee.execute(
            self.protocol,
            sbol3.Agent("agent"),
            id="test_execution",
            parameter_values=[],
        )

        self.assertTrue(ex.parameter_values[1].value.value.lookup(), sbol3.Component)


if __name__ == "__main__":
    unittest.main()
