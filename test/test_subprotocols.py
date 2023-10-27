import unittest

import sbol3

import labop
from labop.execution_engine import ExecutionEngine


class TestSubprotocols(unittest.TestCase):
    def test_subexecutions(self):
        protocol, doc = labop.Protocol.initialize_protocol(
            display_id="protocol",
            name="Protocol",
            namespace="http://bbn.com/scratch/",
        )

        subprotocol1 = labop.Protocol.create_protocol(display_id="sub1", name="sub1")
        subprotocol2 = labop.Protocol.create_protocol(display_id="sub2", name="sub2")
        primitive1 = labop.Primitive("primitive1")

        doc.add(subprotocol1)
        doc.add(subprotocol2)
        doc.add(primitive1)

        protocol.primitive_step(subprotocol1)
        protocol.primitive_step(primitive1)
        protocol.primitive_step(subprotocol2)

        ee = ExecutionEngine()
        ee.specializations[0]._behavior_func_map[
            primitive1.identity
        ] = lambda call, ex: None  # Register custom primitives in the execution engine
        ex = ee.execute(
            protocol,
            sbol3.Agent("test_agent"),
            id="test_execution1",
            parameter_values=[],
        )

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
            # Asynchronous execution will not include subprotocol executions, rather just the tokens inside them that execution.
            subprotocol_executions = ex.get_subprotocol_executions()
            self.assertListEqual(
                [x.protocol.lookup() for x in subprotocol_executions],
                [subprotocol1, subprotocol2],
            )


if __name__ == "__main__":
    unittest.main()
