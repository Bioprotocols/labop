import os

import pytest

import paml
import sbol3
import tyto
import uml
import unittest

from paml_convert.autoprotocol.autoprotocol_specialization import AutoprotocolSpecialization

from paml_convert.autoprotocol.strateos_api import StrateosAPI, StrateosConfig
from paml.execution_engine import ExecutionEngine
from paml_convert.markdown.markdown_specialization import MarkdownSpecialization


class TestConvert(unittest.TestCase):
    @pytest.mark.skip(reason="need to put strateos_secrets.json credentials on github first")
    def test_ludox(self):
        out_dir = "."

        #############################################
        # set up the document
        print('Setting up document')
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')

        protocol_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testfiles", "igem_ludox_test.nt")
        doc.read(protocol_file, 'nt')

        protocol = doc.find("https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018")
        agent = sbol3.Agent("test_agent")

        autoprotocol_output = os.path.join(out_dir, "test_LUDOX_autoprotocol.json")
        secrets_file = os.path.join(os.getcwd(), "../secrets/strateos_secrets.json")
        api = StrateosAPI(cfg=StrateosConfig.from_file(secrets_file))
        resolutions = {
            doc.find("https://bbn.com/scratch/LUDOX"): "rs1b6z2vgatkq7",
            doc.find("https://bbn.com/scratch/ddH2O"): "rs1c7pg8qs22dt",
            "container_id": "ct1g9qsg4wx6gcj"
        }
        autoprotocol_specialization = AutoprotocolSpecialization(autoprotocol_output, api, resolutions)

        markdown_output = os.path.join(out_dir, "test_LUDOX_markdown.md")
        markdown_specialization = MarkdownSpecialization(markdown_output)

        ee = ExecutionEngine(specializations=[autoprotocol_specialization, markdown_specialization])

        parameter_values = [
            paml.ParameterValue(parameter=protocol.get_input("wavelength"),
                                value=uml.LiteralIdentified(value=sbol3.Measure(100, tyto.OM.nanometer)))
        ]

        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)
        assert(os.path.exists(autoprotocol_output))

if __name__ == '__main__':
    unittest.main()