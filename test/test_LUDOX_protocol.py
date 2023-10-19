import logging
import os
import unittest

import labop

logger = logging.getLogger("LUDOX_protocol")
logger.setLevel(logging.INFO)


OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

protocol_def_file = os.path.join(
    os.path.dirname(__file__), "../examples/protocols/ludox/LUDOX_protocol.py"
)


class TestProtocolEndToEnd(unittest.TestCase):
    def create_protocol(self, doc, protocol: labop.Protocol) -> labop.Protocol:
        protocol = labop.execution.harness.ProtocolLoader(
            protocol_def_file, "ludox_protocol"
        ).generate_protocol(doc, protocol)
        return protocol

    def test_create_protocol(self):
        harness = labop.execution.harness.ProtocolHarness(
            clean_output=True,
            base_dir=os.path.dirname(__file__),
            entry_point=self.create_protocol,
            namespace="https://bbn.com/scratch/",
            protocol_name="iGEM_LUDOX_OD_calibration_2018",
            protocol_long_name="iGEM 2018 LUDOX OD calibration protocol",
            protocol_version="1.0",
            protocol_description="""
With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
        """,
            artifacts=[
                labop.execution.harness.ProtocolRubric(
                    filename=os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        "testfiles",
                        "igem_ludox_test.nt",
                    ),
                    # overwrite_rubric=True,  # Used to update rubric
                )
            ],
        )

        harness.run(verbose=True)

        assert len(harness.errors()) == 0, harness.artifacts_results_summary(
            verbose=True
        )


if __name__ == "__main__":
    unittest.main()
