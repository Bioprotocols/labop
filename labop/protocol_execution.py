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
from uml import (
    ActivityNode,
    ActivityParameterNode,
    CallBehaviorAction,
    ControlFlow,
    ControlNode,
    DecisionNode,
    InitialNode,
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
            [start_node] = [n for n in protocol.nodes if type(n) is InitialNode]
        except Exception as e:
            raise Exception(f"Protocol {protocol.identity} has no InitialNode")
        [execution_start_node] = [
            x for x in self.executions if x.node == start_node.identity
        ]  # ActivityNodeExecution
        ordered_execution_nodes = []
        current_execution_node = execution_start_node
        while current_execution_node:
            try:
                [current_execution_node] = [
                    x
                    for x in self.executions
                    for f in x.incoming_flows
                    if f.lookup().token_source == current_execution_node.identity
                ]
                ordered_execution_nodes.append(current_execution_node)
            except ValueError:
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
            o.value.get_value().identity: o.value.get_value().to_dataset()
            for e in calls
            for o in e.get_outputs()
            if isinstance(o.value.get_value(), SampleData)
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
        dot = graphviz.Digraph(
            comment=self.protocol,
            strict=True,
            graph_attr={"rankdir": "TB", "concentrate": "true"},
            node_attr={"ordering": "out"},
        )

        def _make_object_edge(dot, incoming_flow, target, dest_parameter=None):
            flow_source = incoming_flow.lookup().token_source.lookup()
            source = incoming_flow.lookup().edge.lookup().source.lookup()
            value = incoming_flow.lookup().value.get_value()
            is_ref = isinstance(incoming_flow.lookup().value, LiteralReference)
            # value = value.value.lookup() if isinstance(value, LiteralReference) else value.value

            if isinstance(source, Pin):
                src_parameter = (
                    source.get_parent().pin_parameter(source.name).property_value
                )
                src_var = src_parameter.name
            else:
                src_var = ""

            dest_var = dest_parameter.name if dest_parameter else ""

            source_id = source.dot_label(parent_identity=self.protocol)
            if isinstance(source, CallBehaviorAction):
                source_id = f"{source_id}:node"
            target_id = target.dot_label(parent_identity=self.protocol)
            if isinstance(target, CallBehaviorAction):
                target_id = f"{target_id}:node"

            if isinstance(value, sbol3.Identified):
                edge_label = value.display_id  # value.identity
            else:
                edge_label = f"{value}"

            if False and hasattr(value, "to_dot") and not is_ref:
                # Make node for value and connect to source
                value_node_id = value.to_dot(dot, out_dir=out_dir)
                dot.edge(source_id, value_node_id)

            edge_index = incoming_flow.split("ActivityEdgeFlow")[-1]

            edge_label = f"{edge_index}: {edge_label}"

            attrs = {"color": "orange"}
            dot.edge(target_id, source_id, edge_label, _attributes=attrs)

        dot = graphviz.Digraph(
            name=f"cluster_{self.identity}", graph_attr={"label": self.identity}
        )

        # Protocol graph
        protocol_graph = self.protocol.lookup().to_dot(ready=ready, done=done)
        dot.subgraph(protocol_graph)

        if execution_engine and execution_engine.current_node:
            current_node_id = execution_engine.current_node.dot_label(
                parent_identity=self.protocol
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
            exec_target = execution.node.lookup()
            execution_label = ""

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
                target_id = exec_target.dot_label(parent_identity=self.protocol)
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

            for incoming_flow in execution.incoming_flows:
                # Executable Nodes have incoming flow from their input pins and ControlFlows
                flow_source = incoming_flow.lookup().token_source.lookup()
                exec_source = flow_source.node.lookup()
                edge_ref = incoming_flow.lookup().edge
                if edge_ref and isinstance(edge_ref.lookup(), ObjectFlow):
                    if isinstance(exec_target, ActivityParameterNode):
                        # ActivityParameterNodes are ObjectNodes that have a parameter
                        _make_object_edge(
                            dot,
                            incoming_flow,
                            exec_target,
                            dest_parameter=exec_target.parameter.lookup(),
                        )
                    elif isinstance(exec_target, ControlNode):
                        # This in an object flow into the node itself, which happens for ControlNodes
                        _make_object_edge(dot, incoming_flow, exec_target)
                elif isinstance(exec_source, Pin):
                    # This incoming_flow is from an input pin, and need the flow into the pin
                    for into_pin_flow in flow_source.incoming_flows:
                        # source = src_to_pin_edge.source.lookup()
                        # target = src_to_pin_edge.target.lookup()
                        dest_parameter = exec_target.pin_parameter(
                            exec_source.name
                        ).property_value
                        _make_object_edge(
                            dot,
                            into_pin_flow,
                            into_pin_flow.lookup().edge.lookup().target.lookup(),
                            dest_parameter=dest_parameter,
                        )
                elif (
                    isinstance(exec_source, DecisionNode)
                    and edge_ref
                    and isinstance(edge_ref.lookup(), ControlFlow)
                ):
                    _make_object_edge(dot, incoming_flow, exec_target)

        return dot
