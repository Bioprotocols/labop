import unittest

import paml
import uml
import sbol3
from paml.execution_engine import ExecutionEngine
from paml_convert.markdown.markdown_specialization import MarkdownSpecialization
from paml_convert.behavior_specialization import DefaultBehaviorSpecialization


class TestSubprotocols(unittest.TestCase):

    def test_subexecutions(self):
        doc = sbol3.Document()
        sbol3.set_namespace('https://bbn.com/scratch/')

        subprotocol1 = paml.Protocol('sub1')
        subprotocol2 = paml.Protocol('sub2')
        primitive1 = paml.Primitive('primitive1')

        protocol = paml.Protocol('protocol')
        doc.add(subprotocol1)
        doc.add(subprotocol2)
        doc.add(primitive1)
        doc.add(protocol)        
        
        protocol.primitive_step(subprotocol1)
        protocol.primitive_step(primitive1)
        protocol.primitive_step(subprotocol2)
        
        ee = ExecutionEngine()
        ee.specializations[0]._behavior_func_map[primitive1.identity] = lambda call, ex: None  # Register custom primitives in the execution engine
        ex = ee.execute(protocol, sbol3.Agent('test_agent'), id="test_execution1", parameter_values=[ ])
        
        ordered_executions = ex.get_ordered_executions()
        self.assertListEqual([x.identity for x in ordered_executions],
                             ['http://sbols.org/unspecified_namespace/test_execution1/CallBehaviorExecution1',
                              'http://sbols.org/unspecified_namespace/test_execution1/CallBehaviorExecution2',
                              'http://sbols.org/unspecified_namespace/test_execution1/CallBehaviorExecution3'])
        subprotocol_executions = ex.get_subprotocol_executions()
        self.assertListEqual([x.protocol.lookup() for x in subprotocol_executions],
                             [subprotocol1, subprotocol2])
         
if __name__ == '__main__':
    unittest.main()
