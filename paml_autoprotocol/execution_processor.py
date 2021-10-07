from collections import defaultdict
from logging import error, warning
import paml
import sbol3
import uml
from typing import List, Tuple, Dict

from paml_autoprotocol.transcriptic_api import TranscripticAPI
from paml_autoprotocol.behavior_specialization import BehaviorSpecialization
from paml.execution_engine import ExecutionEngine


def perldict():
  return defaultdict(perldict)

class ExecutionProcessor():
    @staticmethod
    def process(execution, specialization: BehaviorSpecialization):
        # HACK just get something in place for viewing the
        # parameter data provided to the execution
        parameters = {}
        for param in execution.parameter_values:
            p = param.parameter.lookup()
            v = param.value.value
            u = param.value.unit if hasattr(param.value, "unit") else ""
            parameters[p.name] = (v, u)

        specialization.on_begin()
        execution_data = {}
        for exec in execution.executions:
            node = exec.node.lookup()
            inflows = []
            execution_data[exec] = (node, inflows)
            for flow_ref in exec.incoming_flows:
                flow = flow_ref.lookup()
                if flow.edge is None:
                    warning("Encountered execution flow NoneType edge")
                    inflows.append((None, None, None, flow.token_source.lookup()))
                    continue
                edge = flow.edge.lookup()
                inflows.append((edge, edge.source.lookup(), edge.target.lookup(), flow.token_source.lookup()))
        
        execution_output = perldict()
        for exec, (node, inflows) in execution_data.items():
            # print(f"EXEC\n  {exec.identity}")
            # print(f"NODE\n  {node.identity}")
            if isinstance(exec, paml.CallBehaviorExecution):
                output = ExecutionProcessor.process_call_behavior(exec, node, inflows, parameters, specialization)
                execution_output.update(output)

            elif isinstance(exec, paml.ActivityNodeExecution):
                output = ExecutionProcessor.process_activity_node_execution(exec, node, inflows, parameters, specialization)
                execution_output.update(output)
            else:
                error(f"Unknown execution type {type(exec)}")
                continue
            # print("=" * 80)
        # print(json.dumps(execution_output, indent=2))
        specialization.on_end()
        return specialization

    @staticmethod
    def process_call_behavior(exec : paml.CallBehaviorExecution,
                              node : uml.ActivityNode,
                              inflows : List[Tuple],
                              parameters : Dict[str, Tuple],
                              specialization: BehaviorSpecialization):
        spec_inputs = {}
        required_inputs = []
        execution_output = perldict()

        for i in node.inputs:
            if isinstance(i, uml.ValuePin):
                value = i.value
                if isinstance(value, uml.LiteralString):
                    # print(f"    {i.name} = {i.value.value}")
                    spec_inputs[i.name] = i.value.value
                elif isinstance(value, uml.LiteralIdentified):
                    measure = value.value
                    if isinstance(measure, sbol3.Measure):
                        spec_inputs[i.name] = (measure.value, value.value.unit)
                        # print(f"    {i.name} = {measure.value} {tyto.OM.get_term_by_uri(value.value.unit)}")
                    else:
                        error(f"{i.name} of unknown type: {type(value)}")
                elif isinstance(value, uml.LiteralReference):
                    # print(f"    {i.name} = {value.value.lookup().types}")
                    spec_inputs[i.name] = value.value.lookup().types
                else:
                    error(f"{i.name} of unknown type: {type(value)}")
            elif isinstance(i, uml.InputPin):
                required_inputs.append(i)
            else:
                error(f"{i.name} of unknown type: {type(i)}")

        for i in required_inputs:
            found_source = False
            for (edge, source, target, token_source) in inflows:
                if i.identity in execution_output[token_source.identity] and not i.name in parameters:
                    i_data = execution_output[token_source.identity][i.identity]
                    # print(f"    {i.name} = {i_data} <--------- {i.identity}")
                    spec_inputs[i.name] = i_data
                    found_source = True
                    continue
            if not found_source:
                if i.name in parameters:
                    spec_inputs[i.name] = parameters[i.name]
                else:
                    # print(f"  {i.name} = UNASSIGNED")
                    spec_inputs[i.name] = None

        # print(f"{node.behavior.rsplit('/', 1)[1]}")
        # print("  INPUT")
        # for k, v in spec_inputs.items():
        #     print(f"    {k} = {v}")

        spec_outputs = {}
        call_outputs = [x for x in exec.call.lookup().parameter_values
                        if x.parameter.lookup().direction == uml.PARAMETER_OUT]
        for o in call_outputs:
            # output = str(uuid.uuid4())
            # print(f"    {o.name} = {output} ---------> {o.identity}")
            # execution_output[exec.identity][o.identity] = output
            spec_outputs[o.parameter.lookup().name] = o.value

        # print("  OUTPUT")
        outputs = specialization.process(node, spec_inputs, spec_outputs)
        for identity, (name, value) in outputs.items():
            # print(f"    {name} = {value}")
            execution_output[exec.identity][identity] = value

        return execution_output

    @staticmethod
    def process_activity_node_execution(exec : paml.CallBehaviorExecution,
                                        node : uml.ActivityNode,
                                        inflows : List[Tuple],
                                        parameters : Dict[str, Tuple],
                                        specialization: BehaviorSpecialization):
        execution_output = perldict()
        for (edge, source, target, token_source) in inflows:
            # print(f"TOKEN\n  {token_source.identity}")
            if isinstance(target, uml.ForkNode):
                # print("INPUT")
                output = execution_output[token_source.identity][source.identity]
                # print(f"  {source.name} = {output} <--------- {source.identity}")
                execution_output[exec.identity][target.identity] = output
                # print("OUTPUT")
                # print(f"  {output} ---------> {target.identity}")
                continue

            # print("INPUT")
            source_data = None
            # if isinstance(source, uml.ActivityParameterNode):
            #     param = source.parameter.lookup()
            #     # name = param.name
            #     value = param.default_value.value
            #     unit = tyto.OM.get_term_by_uri(param.default_value.unit)
            #     source_data = (value, unit)
            #     # print(f"  {name} = {value} {unit}")
            if isinstance(source, uml.ForkNode):
                source_data = execution_output[token_source.identity][source.identity]
                # print(f"  {target.name} = {source_data} <--------- {source.identity}")
            elif isinstance(source, uml.OutputPin):
                source_data = execution_output[token_source.identity][source.identity]
                # print(f"  {target.name} = {source_data} <--------- {source.identity}")
            # elif isinstance(source, uml.CallBehaviorAction):
            #     for out in source.outputs:
            #         if not isinstance(out, uml.ValuePin):
            #             i_data = execution_output[token_source.identity][i.identity]
            #             print(f"  {i.identity}: {i_data}")
            else:
                error(f"ERROR unhandled source: {source.identity}")

            # print("OUTPUT")
            if isinstance(target, uml.InputPin):
                output = source_data  # str(uuid.uuid4())
                execution_output[exec.identity][target.identity] = output
                # print(f"  {output} ---------> {target.identity}")
            else:
                error(f"ERROR unhandled target: {target.identity}")

        return execution_output