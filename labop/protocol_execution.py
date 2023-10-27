"""
The ProtocolExecution class defines the functions corresponding to the dynamically generated labop class ProtocolExecution
"""

import datetime
import json
from typing import List

import graphviz
import sbol3

import labop.inner as inner
import uml
from labop.execution_engine_utils import (
    JSONProtocolExecutionExtractor,
    ProtocolExecutionExtractor,
)
from uml import (
    PARAMETER_IN,
    PARAMETER_OUT,
    ActivityNode,
    ActivityParameterNode,
    CallBehaviorAction,
    ControlFlow,
    ControlNode,
    DecisionNode,
    FinalNode,
    InitialNode,
    InputPin,
    LiteralReference,
    ObjectFlow,
    Pin,
)

from .behavior_execution import BehaviorExecution
from .call_behavior_execution import CallBehaviorExecution
from .material import Material
from .protocol import Protocol
from .sample_data import SampleData


class ProtocolExecution(inner.ProtocolExecution, BehaviorExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_ordered_executions(self):
        protocol = self.protocol.lookup()
        try:
            start_node = next(n for n in protocol.nodes if type(n) is InitialNode)
        except Exception as e:
            raise Exception(f"Protocol {protocol.identity} has no InitialNode")
        execution_start_node = next(
            x for x in self.executions if x.node == start_node.identity
        )  # ActivityNodeExecution
        ordered_execution_nodes = []
        current_execution_node = execution_start_node
        while current_execution_node:
            try:
                current_execution_node = next(
                    x
                    for x in self.executions
                    for f in x.incoming_flows
                    if f.lookup().token_source == current_execution_node.identity
                )
                ordered_execution_nodes.append(current_execution_node)
            except ValueError:
                current_execution_node = None
            except StopIteration:
                current_execution_node = None
        return ordered_execution_nodes

    def get_subprotocol_executions(self):
        ordered_subprotocol_executions = []
        ordered_execution_nodes = self.get_ordered_executions()
        ordered_behavior_nodes = [
            x.node.lookup().behavior.lookup()
            for x in ordered_execution_nodes
            if isinstance(x, CallBehaviorExecution)
        ]
        ordered_subprotocols = [
            x.identity for x in ordered_behavior_nodes if isinstance(x, Protocol)
        ]
        ordered_subprotocol_executions = [
            o
            for x in ordered_subprotocols
            for o in self.document.objects
            if type(o) is ProtocolExecution and o.protocol == x
        ]
        return ordered_subprotocol_executions

    def set_data(self, dataset):
        """
        Overwrite execution trace values based upon values provided in data
        """
        for k, v in dataset.items():
            sample_data = self.document.find(k)
            sample_data.values = json.dumps(v.to_dict())

    def get_data(self):
        """
        Gather labop.SampleData outputs from all CallBehaviorExecutions into a dataset
        """
        calls = [e for e in self.executions if isinstance(e, CallBehaviorExecution)]
        datasets = {
            val.get_value().identity: val.get_value().to_dataset()
            for e in calls
            for o in e.get_outputs()
            for val in o.get_value()
            if isinstance(val.get_value(), SampleData)
        }

        return datasets

    def aggregate_child_materials(self):
        """Merge the consumed material from children, adding a fresh Material for each to this record.

        Parameters
        ----------
        self: ProtocolExecution object
        """
        child_materials = [
            e.call.consumed_material
            for e in self.executions
            if isinstance(e, CallBehaviorExecution)
            and hasattr(e.call, "consumed_material")
        ]
        specifications = {m.specification for m in child_materials}
        self.consumed_material = (
            Material(
                s,
                self.sum_measures(
                    [m.amount for m in child_materials if m.specification == s]
                ),
            )
            for s in specifications
        )

    def sum_measures(self, measure_list):
        """Add a list of measures and return a fresh measure
        Note: requires that all have the same unit and types

        Parameters
        ----------
        measure_list of SBOL Measure objects

        Returns
        -------
        New Measure object with the sum of input measure amounts
        """
        prototype = measure_list[0]
        if not all(
            m.types == prototype.types and m.unit == prototype.unit
            for m in measure_list
        ):
            raise ValueError(
                f"Can only merge measures with identical units and types: {([m.value, m.unit, m.types] for m in measure_list)}"
            )
        total = sum(m.value for m in measure_list)
        return sbol3.Measure(value=total, unit=prototype.unit, types=prototype.types)

    def to_dot(
        self,
        execution_engine=None,
        ready: List[ActivityNode] = [],
        done=set([]),
        out_dir="out",
    ):
        """
        Create a dot graph that illustrates edge values appearing the execution of the protocol.
        :param self:
        :return: graphviz.Digraph
        """
        # dot = graphviz.Digraph(
        #     comment=self.protocol,
        #     strict=True,
        #     graph_attr={"rankdir": "TB", "concentrate": "true"},
        #     node_attr={"ordering": "out"},
        # )

        dot = graphviz.Digraph(
            name=f"cluster_{self.identity}", graph_attr={"label": self.identity}
        )

        # Protocol Invocation
        execution_context = self.execution_context

        # Protocol graph
        protocol = self.protocol.lookup()
        protocol_graph = protocol.to_dot(ready=ready, done=done)
        dot.subgraph(protocol_graph)

        if execution_engine and execution_engine.current_node:
            current_node_id = execution_engine.current_node.dot_label(
                namespace=self.namespace
            )
            current_node_id = f"{current_node_id}:node"
            dot.edge(
                current_node_id,
                current_node_id,
                _attributes={
                    "tailport": "w",
                    "headport": "w",
                    "taillabel": "current_node",
                    "color": "red",
                },
            )

        # Execution graph
        for execution in self.executions:
            execution_node = execution.get_node()
            execution_label = ""

            node_in_outer_context = execution_node.get_parent() == self or (
                isinstance(execution_node, Pin)
                and execution_node.get_parent().get_parent() == self
            )
            if node_in_outer_context:
                # If node is not part of protocol, then its part of the invocation of the protocol and isn't drawn by the protocol to_dot()
                incoming_edges = execution_context.incoming_edges(execution_node)

                # Pins are drawn as part of CallBehaviorAction
                if not isinstance(execution_node, Pin):
                    _ = execution_node.to_dot(
                        dot,
                        namespace=self.namespace,
                        done=done,
                        ready=ready,
                        incoming_edges=incoming_edges,
                    )

                # Add incoming edges to execution_node
                # if not isinstance(execution_node, FinalNode):
                for edge in incoming_edges:
                    edge_source_in_outer_context = (
                        edge.get_source().get_parent() == self
                        or (
                            isinstance(execution_node, Pin)
                            and edge.get_source().get_parent().get_parent() == self
                        )
                    )
                    if (
                        edge.dot_plottable()
                        and edge.get_parent() == self
                        and edge_source_in_outer_context
                    ):
                        edge.to_dot(dot, namespace=self.namespace)

            #     # Add outgoing edges from execution_node
            #     outgoing_edges = execution_context.outgoing_edges(
            #         execution_node
            #     )
            #     for edge in outgoing_edges:
            #         if edge.dot_plottable() and not (
            #             edge.get_target() in execution_context.nodes
            #         ):
            #             edge.to_dot(dot, namespace=self.namespace)

            # # Add incoming edges to execution_node
            # for incoming_flow in execution.get_incoming_flows():
            #     # Executable Nodes have incoming flow from their input pins and ControlFlows
            #     # parameter = target_node.get_parameter()
            #     if isinstance(incoming_flow.get_edge(), ObjectFlow):
            #         if (
            #             isinstance(execution_node, ActivityParameterNode)
            #             or isinstance(execution_node, ControlNode)
            #             or isinstance(execution_node, InputPin)
            #         ):
            #             incoming_flow.to_dot(
            #                 dot,
            #                 execution_node,
            #                 self.namespace,
            #                 out_dir=out_dir,
            #                 color="orange"
            #                 # dest_parameter=parameter,
            #             )

            # Make a self loop that includes the and start and end time.
            if isinstance(execution, CallBehaviorExecution):
                time_format = "%H:%M:%S"
                start_time = datetime.datetime.strftime(
                    execution.call.lookup().start_time, time_format
                )
                end_time = datetime.datetime.strftime(
                    execution.call.lookup().end_time, time_format
                )
                if start_time == end_time:
                    execution_label += f"[{start_time}]"
                else:
                    execution_label += f"[{start_time},\n  {end_time}]"
                target_id = execution_node.dot_label(namespace=self.namespace)
                target_id = f"{target_id}:node"
                dot.edge(
                    target_id,
                    target_id,
                    _attributes={
                        "tailport": "w",
                        "headport": "w",
                        "taillabel": execution_label,
                        "color": "invis",
                    },
                )

            for incoming_flow in execution.get_incoming_flows():
                # Executable Nodes have incoming flow from their input pins and ControlFlows
                source_execution = incoming_flow.get_source()
                source_node = source_execution.get_node()
                edge_ref = incoming_flow.get_edge()
                parameter = execution_node.get_parameter()
                if isinstance(edge_ref, ObjectFlow):
                    if (
                        isinstance(execution_node, ActivityParameterNode)
                        or isinstance(execution_node, ControlNode)
                        or isinstance(execution_node, InputPin)
                    ):
                        incoming_flow.to_dot(
                            dot,
                            execution_node,
                            self.namespace,
                            dest_parameter=parameter,
                            out_dir=out_dir,
                        )

                elif isinstance(source_node, DecisionNode) and isinstance(
                    edge_ref, ControlFlow
                ):
                    incoming_flow.to_dot(
                        dot, execution_node, self.namespace, out_dir=out_dir
                    )
                elif (
                    isinstance(edge_ref, ControlFlow)
                    and source_node.get_parent() != execution_node.get_parent()
                ):
                    # Plot ControlFlow for subprotocol invocation
                    incoming_flow.to_dot(
                        dot,
                        execution_node,
                        self.namespace,
                        out_dir=out_dir,
                        color="blue",
                        reverse=True,
                    )

        return dot

    def backtrace(
        self,
        stack=None,
        extractor: ProtocolExecutionExtractor = JSONProtocolExecutionExtractor(),
    ):
        stack = self.executions if stack is None else stack
        if len(stack) == 0:
            return set([]), []
        else:
            tail = stack[-1]
            head = stack[:-1]
            nodes, head = self.backtrace(stack=head)
            nodes.add(tail.node.lookup())
            head += [extractor.extract_record(tail)]
            return nodes, head

    def to_json(self):
        """
        Convert Protocol Execution to JSON
        """
        p_json = self.backtrace(extractor=JSONProtocolExecutionExtractor())[1]
        return json.dumps(p_json)

    def unbound_inputs(self):
        unbound_input_parameters = [
            p.node.lookup().parameter.lookup().property_value
            for p in self.executions
            if isinstance(p.node.lookup(), ActivityParameterNode)
            and p.node.lookup().parameter.lookup().property_value.direction
            == PARAMETER_IN
            and p.node.lookup().parameter.lookup().property_value
            not in [
                pv.parameter.lookup().property_value for pv in self.parameter_values
            ]
        ]
        return unbound_input_parameters

    def unbound_outputs(self):
        unbound_output_parameters = [
            p.node.lookup().parameter.lookup().property_value
            for p in self.executions
            if isinstance(p.node.lookup(), ActivityParameterNode)
            and p.node.lookup().parameter.lookup().property_value.direction
            == PARAMETER_OUT
            and p.node.lookup().parameter.lookup().property_value
            not in [
                pv.parameter.lookup().property_value for pv in self.parameter_values
            ]
        ]
        return unbound_output_parameters
