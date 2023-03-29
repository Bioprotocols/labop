from typing import Iterable

import sbol3

from uml import (
    ActivityEdge,
    ActivityParameterNode,
    CallBehaviorAction,
    OutputPin,
    ValuePin,
)

from . import ParameterValue, ProtocolExecution


class ExecutionContext(object):
    """
    An ExecutionContext is a scope of execution of an Activity.  It is used to hold tokens occurring in the context and disambiguate alternative executions of the same Activity.
    """

    def __init__(
        self,
        execution_trace: ProtocolExecution,
        protocol,
        parameter_values,
        parent_context=None,
    ):
        self.parent_context = parent_context
        self.protocol = protocol
        self.parameter_values = parameter_values
        self.candidate_clusters = {}
        self.incoming_edge_tokens = {}  # Maps node -> edge -> value
        self.input_edges = []
        self.output_edges = []
        self.tokens = []  # no tokens to start
        self.execution_trace = execution_trace
        if parent_context is None:
            self.call_protocol_node = CallBehaviorAction(behavior=self.protocol)
            execution_trace.activity_call_node.append(self.call_protocol_node)
            # execution_trace.executions.append(ActivityNodeExecution(node=self.call_protocol_node))
            self.create_invocation_pins()

        # Setup incoming edge map for each node
        self.incoming_edge_tokens[self.call_protocol_node] = {}
        for node in self.protocol.nodes:
            self.incoming_edge_tokens[node] = {}
            for e in self.protocol.incoming_edges(node):
                self.incoming_edge_tokens[node][e] = []
            if isinstance(node, ActivityParameterNode) and node.is_input():
                # if matching input parameters, then add dummy edge value
                param_values = [
                    pv
                    for pv in self.parameter_values
                    if pv.get_parameter() == node.get_parameter()
                ]
                for pv in param_values:
                    self.incoming_edge_tokens[node][pv.get_parameter()] = pv.value()

    def create_invocation_pins(self):
        # Create invocation edge to InitialNode
        e = ActivityEdge(source=self.call_protocol_node, target=self.protocol.initial())
        self.execution_trace.activity_call_edge.append(e)

        input_map = ParameterValue.parameter_value_map(self.parameter_values)
        for i in self.protocol.get_inputs():
            if i.name in input_map:
                values = input_pin_literals[i.property_value.name]
                # TODO: type check relationship between value and parameter type specification

                # If the value is a singleton, then wrap it in an iterable
                if not isinstance(values, Iterable) or isinstance(values, str):
                    values = [values]

                # Now create pins for all the input values
                for value in values:
                    if isinstance(value, sbol3.TopLevel) and not value.document:
                        self.document.add(value)
                    value_pin = ValuePin(
                        name=i.property_value.name,
                        is_ordered=i.property_value.is_ordered,
                        is_unique=i.property_value.is_unique,
                        value=literal(value),
                    )
                    self.call_protocol_node.get_inputs.append(value_pin)
                    e = ActivityEdge(source=value_pin, target=self.call_protocol_node)
                    self.execution_trace.activity_call_edge.append(e)
                    self.input_edges.append(e)
        for o in self.protocol.get_outputs():
            output_pin = OutputPin(
                name=o.name,
                is_ordered=o.is_ordered,
                is_unique=o.is_unique,
            )
            self.call_protocol_node.get_outputs().append(output_pin)
            e = ActivityEdge(source=self.call_protocol_node, target=output_pin)
            self.execution_trace.activity_call_edge.append(e)
            self.output_edges.append(e)

    def initialize_entry(self):

        return [self.call_protocol_node]

    def outgoing_edges(self, node):
        out_edges = []
        if node in self.protocol.nodes:
            out_edges += self.protocol.outgoing_edges(node)
            # FIXME if node is a CallBehaviorAction, then ensure call edges are included in outgoing
        if node == self.call_protocol_node:
            out_edges += self.execution_trace.activity_call_edge
        return out_edges
