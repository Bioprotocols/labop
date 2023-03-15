import filecmp
import os
import tempfile
import unittest

import sbol3
import tyto

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert import MarkdownSpecialization, OpentronsSpecialization
from labop_convert.autoprotocol.autoprotocol_specialization import (
    AutoprotocolSpecialization,
)
from labop_convert.autoprotocol.strateos_api import StrateosAPI, StrateosConfig


class TestConvert(unittest.TestCase):
    def _run_execution(self, doc, specializations):
        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")

        #############################################
        # Execution Configuration
        ee = ExecutionEngine(specializations=specializations)
        agent = sbol3.Agent("test_agent")
        parameter_values = [
            labop.ParameterValue(
                parameter=protocol.get_input("wavelength"),
                value=uml.LiteralIdentified(
                    value=sbol3.Measure(100, tyto.OM.nanometer)
                ),
            )
        ]

        #############################################
        # Execute Protocol and Convert
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution",
            parameter_values=parameter_values,
        )

    @unittest.skip(
        reason="need to put strateos_secrets.json credentials on github first"
    )
    def test_igem_ludox(self):
        #############################################
        # Set up the document
        print("Setting up document")
        doc = sbol3.Document()
        sbol3.set_namespace("https://bbn.com/scratch/")

        #############################################
        # Get the protocol
        protocol_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_test.nt",
        )
        doc.read(protocol_file, "nt")
        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")
        #############################################
        # Autoprotocol and Strateos Configuration
        autoprotocol_output = os.path.join(
            tempfile.gettempdir(), "igem_ludox_autoprotocol.json"
        )
        secrets_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../secrets/strateos_secrets.json",
        )
        api = StrateosAPI(cfg=StrateosConfig.from_file(secrets_file))
        resolutions = {
            doc.find("https://bbn.com/scratch/LUDOX"): "rs1b6z2vgatkq7",
            doc.find("https://bbn.com/scratch/ddH2O"): "rs1c7pg8qs22dt",
            "container_id": "ct1g9qsg4wx6gcj",
        }
        autoprotocol_specialization = AutoprotocolSpecialization(
            autoprotocol_output, api, resolutions
        )

        #############################################
        # Execution Configuration
        ee = ExecutionEngine(specializations=[autoprotocol_specialization])
        agent = sbol3.Agent("test_agent")
        parameter_values = [
            labop.ParameterValue(
                parameter=protocol.get_input("wavelength"),
                value=uml.LiteralIdentified(
                    value=sbol3.Measure(100, tyto.OM.nanometer)
                ),
            )
        ]

        #############################################
        # Execute Protocol and Convert
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution",
            parameter_values=parameter_values,
        )

        #############################################
        # Check outputs match

        # Check Autoprotocol output
        autoprotocol_comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_autoprotocol.json",
        )
        # Uncomment next two lines to write the rubric file (Careful!)
        # with open(autoprotocol_comparison_file, "w") as out_file, open(autoprotocol_output) as in_file:
        #     out_file.write(in_file.read())

        print(f"Comparing against {autoprotocol_comparison_file}")
        assert filecmp.cmp(
            autoprotocol_output, autoprotocol_comparison_file
        ), "Autoprotocol files are not identical"
        print("File identical with test file")

    def test_igem_ludox_markdown(self):
        #############################################
        # Set up the document
        print("Setting up document")
        doc = sbol3.Document()
        sbol3.set_namespace("https://bbn.com/scratch/")

        #############################################
        # Get the protocol
        protocol_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_test.nt",
        )
        doc.read(protocol_file, "nt")
        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")

        #############################################
        # Markdown Configuration
        markdown_output = os.path.join(tempfile.gettempdir(), "igem_ludox_markdown.md")
        markdown_specialization = MarkdownSpecialization(markdown_output)

        self._run_execution(doc, [markdown_specialization])

        #############################################
        # Check outputs match

        # Check Markdown output
        markdown_comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_markdown.md",
        )
        # Uncomment next two lines to write the rubric file (Careful!)
        # with open(markdown_comparison_file, "w") as out_file, open(markdown_output) as in_file:
        #     out_file.write(in_file.read())

        print(f"Comparing against {markdown_comparison_file}")
        assert filecmp.cmp(
            markdown_output, markdown_comparison_file
        ), "Markdown files are not identical"
        print("File identical with test file")

    def test_igem_ludox_opentrons(self):
        #############################################
        # Set up the document
        print("Setting up document")
        doc = sbol3.Document()
        sbol3.set_namespace("https://bbn.com/scratch/")

        #############################################
        # Get the protocol
        protocol_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_test.nt",
        )
        doc.read(protocol_file, "nt")
        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")

        #############################################
        # Opentrons Configuration
        opentrons_output = os.path.join(
            tempfile.gettempdir(), "igem_ludox_opentrons.json"
        )
        opentrons_specialization = OpentronsSpecialization(opentrons_output)

        #############################################
        # Execution Configuration
        ee = ExecutionEngine(specializations=[opentrons_specialization])
        agent = sbol3.Agent("test_agent")
        parameter_values = [
            labop.ParameterValue(
                parameter=protocol.get_input("wavelength"),
                value=uml.LiteralIdentified(
                    value=sbol3.Measure(100, tyto.OM.nanometer)
                ),
            )
        ]

        #############################################
        # Execute Protocol and Convert
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution",
            parameter_values=parameter_values,
        )

        #############################################
        # Check outputs match

        # Check Opentrons output
        opentrons_comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "ludox_ot2.py",
        )
        # Uncomment next two lines to write the rubric file (Careful!)
        # with open(opentrons_comparison_file, "w") as out_file, open(opentrons_output) as in_file:
        #     out_file.write(in_file.read())

        print(f"Comparing against {opentrons_comparison_file}")
        assert filecmp.cmp(
            opentrons_output, opentrons_comparison_file
        ), "Markdown files are not identical"
        print("File identical with test file")


if __name__ == "__main__":
    unittest.main()
