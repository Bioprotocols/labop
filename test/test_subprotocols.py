import os
import unittest

import sbol3

import labop
from labop.execution.harness import ProtocolExecutionNTuples


class TestSubprotocols(unittest.TestCase):
    def generate_protocol(
        self, doc: sbol3.Document, protocol: labop.Protocol
    ) -> labop.Protocol:
        subprotocol1 = labop.Protocol.create_protocol(display_id="sub1", name="sub1")
        subprotocol2 = labop.Protocol.create_protocol(display_id="sub2", name="sub2")
        primitive1 = labop.Primitive("primitive1")

        doc.add(subprotocol1)
        doc.add(subprotocol2)
        doc.add(primitive1)

        protocol.primitive_step(subprotocol1)
        protocol.primitive_step(primitive1)
        protocol.primitive_step(subprotocol2)

        return protocol

    def test_subexecutions(self):
        harness = labop.execution.harness.ProtocolHarness(
            namespace="http://bbn.com/scratch/",
            base_dir=os.path.join(os.path.dirname(__file__), "out"),
            entry_point=self.generate_protocol,
            execution_id="test_execution1",
        )
        execution_artifacts = harness.artifacts_of_type(ProtocolExecutionNTuples)

        # execution_artifact.execution_engine.specializations[0]._behavior_func_map[
        #     primitive1.identity
        # ] = (
        #     lambda call, ex: None
        # )  # Register custom primitives in the execution engine
        harness.run()
        ea = next(iter(execution_artifacts))
        ex = ea.execution
        ee = ea.execution_engine

        ordered_executions = ex.get_ordered_executions()
        self.assertListEqual(
            [x.identity for x in ordered_executions],
            [
                "http://bbn.com/scratch/test_execution1/CallBehaviorExecution2",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution3",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution4",
                "http://bbn.com/scratch/test_execution1/CallBehaviorExecution3",
                "http://bbn.com/scratch/test_execution1/CallBehaviorExecution4",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution5",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution6",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution7",
                "http://bbn.com/scratch/test_execution1/ActivityNodeExecution8",
            ],
        )
        if not ee.is_asynchronous:
            # FIXME There is no synchronous mode at this time and the subprotocol executions are part of the top-level execution

            # Asynchronous execution will not include subprotocol executions, rather just the tokens inside them that execution.
            protocol = ex.get_protocol()
            behaviors = protocol.get_behaviors()
            subprotocols = [b for b in behaviors if isinstance(b, labop.Protocol)]
            subprotocols.sort(key=lambda x: x.identity)
            subprotocol_executions = ex.get_subprotocol_executions()
            self.assertListEqual(
                [x.get_protocol for x in subprotocol_executions],
                subprotocols,
            )


if __name__ == "__main__":
    unittest.main()
