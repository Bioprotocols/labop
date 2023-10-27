from typing import Dict, Iterable, List, Optional

import sbol3

from uml import (
    Action,
    Activity,
    ActivityEdge,
    ActivityNode,
    ActivityParameterNode,
    CallBehaviorAction,
    ControlFlow,
    LiteralSpecification,
    ObjectFlow,
    OutputPin,
    Pin,
    ValuePin,
    literal,
)
from uml.activity import Activity
from uml.activity_edge import ActivityEdge
from uml.behavior import Behavior
from uml.final_node import FinalNode
from uml.initial_node import InitialNode

from .call_behavior_execution import CallBehaviorExecution
from .parameter_value import ParameterValue


class ExecutionContext(object):
    """
    An ExecutionContext is a scope of execution of an Activity.  It is used to hold tokens occurring in the context and disambiguate alternative executions of the same Activity.
    """

    def __init__(
        self,
        execution_trace: "ProtocolExecution",
        activity: Activity,
        parameter_values: List[ParameterValue],
        parent_context: Optional["ExecutionContext"] = None,
    ):
        self.parent_context = parent_context

        self.parameter_values = parameter_values
        self.candidate_clusters = {}
        self.incoming_edge_tokens: Dict[
            ActivityNode, Dict[ActivityEdge, LiteralSpecification]
        ] = {}  # Maps node -> edge -> value
        self.input_edges = []  # FIXME remove?
        self.output_edges = []  # FIXME remove?
        self.tokens = []  # no tokens to start
        self.ready = []
        self.nodes = []
        """Reference to the shared execution_trace """
        self.execution_trace = execution_trace
        self.call_pins = []  # FIXME remove?

        nodes_to_initialize: List[ActivityNode] = []

        if parent_context is None:
            self.execution_trace.execution_context = self  # Needed for to_dot()
            self.activity = None
            # If there is no parent context, then initialize a CallBehaviorAction that is calling the Activity
            # This CallBehaviorAction will later be expanded into a new ExecutionContext that includes the Activity ActivityNodes with ExecutionContext.invoke_activity.
            self.initial_node = InitialNode()
            self.invoke_activity_node = CallBehaviorAction(behavior=activity)
            self.final_node = FinalNode()
            execution_trace.activity_call_node.append(self.invoke_activity_node)
            execution_trace.activity_call_node.append(self.initial_node)
            execution_trace.activity_call_node.append(self.final_node)

            self.execution_trace.activity_call_edge.append(
                ControlFlow(source=self.initial_node, target=self.invoke_activity_node)
            )
            self.execution_trace.activity_call_edge.append(
                ControlFlow(source=self.invoke_activity_node, target=self.final_node)
            )
            self.execution_trace.activity_call_edge.append(
                ControlFlow(source=self.initial_node, target=self.final_node)
            )

            # self.invoke_activity_node.is_invocation = True
            # self.return_activity = CallBehaviorAction(
            #     behavior=self.activity
            # )
            # self.return_activity.is_return = True
            # execution_trace.activity_call_node.append(self.return_activity)
            # # execution_trace.executions.append(ActivityNodeExecution(node=self.call_protocol_node))
            self.create_invocation_pins(activity)
            self.ready.append(self.initial_node)
            nodes_to_initialize += execution_trace.activity_call_node
            nodes_to_initialize += self.call_pins
            self.nodes = [
                self.initial_node,
                self.final_node,
                self.invoke_activity_node,
            ] + self.call_pins
        else:
            self.activity = activity
            nodes_to_initialize += self.activity.nodes
            nodes_to_initialize += [
                o
                for n in self.activity.nodes
                if hasattr(n, "outputs")
                for o in n.outputs
            ]
            nodes_to_initialize += [
                i for n in self.activity.nodes if hasattr(n, "inputs") for i in n.inputs
            ]
            self.nodes = list(self.activity.nodes) + [
                p
                for n in [cba for cba in self.activity.nodes if isinstance(cba, Action)]
                for p in list(n.get_inputs()) + list(n.get_outputs())
            ]

        # Setup incoming edge map for each node
        for node in nodes_to_initialize:
            self.incoming_edge_tokens[node] = {}
            for e in self.incoming_edges(node):
                self.incoming_edge_tokens[node][e] = []
            # if isinstance(node, ActivityParameterNode) and node.is_input():
            #     # if matching input parameters, then add dummy edge value
            #     param_values = [
            #         pv
            #         for pv in self.parameter_values
            #         if pv.get_parameter() == node.get_parameter()
            #     ]
            #     for pv in param_values:
            #         self.incoming_edge_tokens[node][
            #             pv.get_parameter()
            #         ] = pv.value()

    def create_invocation_pins(self, activity: Behavior):
        # Make pins for the activity

        input_map = ParameterValue.parameter_value_map(self.parameter_values)
        for i in activity.get_parameters(input_only=True):
            if i.name in input_map:
                values = input_map[i.name]
                # TODO: type check relationship between value and parameter type specification

                # If the value is a singleton, then wrap it in an iterable
                if not isinstance(values, Iterable) or isinstance(values, str):
                    values = [values]

                # Now create pins for all the input values
                for value in values:
                    reference = False
                    if isinstance(value, sbol3.TopLevel) and not value.document:
                        activity.document.add(value)
                    else:
                        reference = True
                    value_pin = ValuePin(
                        name=i.name,
                        is_ordered=i.is_ordered,
                        is_unique=i.is_unique,
                        value=literal(value, reference=reference),
                    )
                    self.invoke_activity_node.get_inputs().append(value_pin)
                    self.call_pins.append(value_pin)  # FIXME remove?

                    # Connect to CallBehaviorAction
                    input = ObjectFlow(
                        source=value_pin, target=self.invoke_activity_node
                    )
                    self.execution_trace.activity_call_edge.append(input)
                    self.input_edges.append(input)  # FIXME remove?
        for o in activity.get_parameters(output_only=True):
            output_pin = OutputPin(
                name=o.name,
                is_ordered=o.is_ordered,
                is_unique=o.is_unique,
            )
            self.invoke_activity_node.get_outputs().append(output_pin)
            self.call_pins.append(output_pin)  # FIXME remove?

            # Connect to CallBehaviorAction
            end = ObjectFlow(source=self.invoke_activity_node, target=output_pin)
            self.execution_trace.activity_call_edge.append(end)
            self.output_edges.append(end)  # FIXME remove?

    def outgoing_edges(self, node):
        out_edges = []
        # if node in self.activity.nodes:
        if self.activity:
            out_edges += self.activity.outgoing_edges(node)
        out_edges += [
            e for e in self.execution_trace.activity_call_edge if e.get_source() == node
        ]
        return out_edges

    def incoming_edges(self, node):
        in_edges = []
        # if node in self.activity.nodes:
        if self.activity:
            in_edges += self.activity.incoming_edges(node)
        in_edges += [
            e for e in self.execution_trace.activity_call_edge if e.get_target() == node
        ]
        return in_edges

    def get_invocation_edge(self, source: ActivityNode, target: ActivityNode):
        try:
            return next(
                iter(
                    [
                        e
                        for e in self.execution_trace.activity_call_edge
                        if e.get_source() == source and e.get_target() == target
                    ]
                )
            )
        except StopIteration:
            raise Exception(f"Could not find invocation edge from {source}")

    def get_nodes(self):
        nodes = []
        if self.activity:
            nodes += self.activity.get_nodes()
        else:
            nodes += [
                self.initial_node,
                self.final_node,
                self.invoke_activity_node,
            ]
        return nodes

    def get_parameter_values(self):
        # Add top execution_context parameter_values to execution_trace
        invocation_pin_executions = [
            e
            for e in self.execution_trace.executions
            if e.get_node().get_parent() == self.invoke_activity_node
            and isinstance(e.get_node(), Pin)
        ]
        parameter_values = [
            ParameterValue(
                value=literal(v, reference=True),
                parameter=pin_execution.get_node().get_parameter(
                    ordered=True
                ),  # f.get_edge().get_source().get_parameter(),
            )
            for pin_execution in invocation_pin_executions
            for f in pin_execution.get_incoming_flows()
            for v in f.get_value()
            if isinstance(f.get_edge(), ObjectFlow)
            and isinstance(f.get_edge().get_source(), ActivityParameterNode)
        ]
        self.parameter_values += parameter_values
        return self.parameter_values

    def invoke_activity(self, call_behavior_execution: CallBehaviorExecution):
        activity: Activity = call_behavior_execution.get_node().get_behavior()
        parameter_values: List[
            ParameterValue
        ] = call_behavior_execution.get_call().parameter_values
        call_behavior_action = call_behavior_execution.get_node()
        # Ensure that the behavior has an initial and final node
        # Order the final node after the last_step (if present)
        activity.initial()
        if hasattr(activity, "last_step"):
            activity.order(activity.last_step, activity.final())
        else:
            activity.order(activity.initial(), activity.final())

        activity_context = ExecutionContext(
            self.execution_trace,
            activity,
            parameter_values,
            parent_context=self,
        )

        # # Make an invocation node for the activity
        # activity_context.invoke_activity_node = CallBehaviorAction(behavior=behavior)
        # activity_context.invoke_activity_node.is_invocation = True
        # activity_context.return_activity = CallBehaviorAction(
        #     behavior=behavior
        # )
        # activity_context.return_activity.is_return = True

        # execution_trace.activity_call_node.append(self.invoke_activity_node)
        # execution_trace.activity_call_node.append(self.return_activity)

        # However, connect each ObjectFlow to the corresponding ActivityParameterNode
        for edge in self.incoming_edges(call_behavior_action):
            if isinstance(edge, ObjectFlow):
                try:
                    activity_parameter_node = next(
                        iter(
                            [
                                n
                                for n in activity.get_nodes(
                                    name=edge.get_source().name,
                                    node_type=ActivityParameterNode,
                                )
                                if n.is_input()
                            ]
                        )
                    )
                except StopIteration:
                    raise Exception(
                        f"Could not find ActivityNodeParameter {edge.get_source().name} in {activity}"
                    )
                input_flow = ObjectFlow(
                    source=edge.get_source(), target=activity_parameter_node
                )
                self.execution_trace.activity_call_edge.append(input_flow)
                activity_context.incoming_edge_tokens[activity_parameter_node][
                    input_flow
                ] = []
                self.input_edges.append(input_flow)

        # parent.CBA -> child.InitialNode
        init = activity_context.activity.initial()
        start = ControlFlow(
            source=call_behavior_action,
            target=init,
        )
        activity_context.execution_trace.activity_call_edge.append(start)
        activity_context.incoming_edge_tokens[init][start] = []

        # Control edges with call_behavior_action as source are replicated with the activity_context.activity as source
        for edge in self.outgoing_edges(call_behavior_action):
            if isinstance(edge, ControlFlow):
                t = edge.get_target()
                # if isinstance(t, FinalNode):
                # child.FinalNode -> parent.cba.controlflow.target
                if t in self.get_nodes():
                    end = ControlFlow(
                        source=activity_context.activity.final(),
                        target=t,
                    )
                    activity_context.execution_trace.activity_call_edge.append(end)
                    if t not in self.incoming_edge_tokens:
                        self.incoming_edge_tokens[t] = {}
                    self.incoming_edge_tokens[t][end] = []

            elif isinstance(edge, ObjectFlow):
                try:
                    activity_parameter_node = next(
                        iter(
                            [
                                n
                                for n in activity.get_nodes(
                                    name=edge.get_target().name,
                                    node_type=ActivityParameterNode,
                                )
                                if n.is_output()
                            ]
                        )
                    )
                except StopIteration:
                    raise Exception(
                        f"Could not find ActivityNodeParameter {edge.get_source().name} in {activity}"
                    )

                output = ObjectFlow(
                    source=activity_parameter_node,
                    target=call_behavior_action.output_pin(
                        activity_parameter_node.get_parameter().name
                    ),
                )
                self.execution_trace.activity_call_edge.append(output)
                self.incoming_edge_tokens[output.get_target()][output] = []
                self.output_edges.append(output)
        return activity_context

    def to_dot(
        self,
        execution_engine=None,
        ready: List[ActivityNode] = [],
        done=set([]),
        out_dir="out",
    ):
        pass
