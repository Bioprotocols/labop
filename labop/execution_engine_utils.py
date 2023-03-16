import logging
import uuid
from abc import abstractmethod
from typing import Callable, List, Set

import sbol3

import labop
import uml
from labop.execution_engine import ExecutionEngine
from labop_convert.behavior_specialization import BehaviorSpecialization

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class ExecutionIssue(object):
    pass


class ExecutionWarning(ExecutionIssue):
    pass


class ExecutionError(ExecutionIssue):
    pass


@abstractmethod
def activity_node_enabled(
    self: uml.ActivityNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    """Check whether all incoming edges have values defined by a token in tokens and that all value pin values are
    defined.

    Parameters
    ----------
    self: node to be executed
    tokens: current list of pending edge flows

    Returns
    -------
    bool if self is enabled
    """
    protocol = self.protocol()
    incoming_controls = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)
    }
    incoming_objects = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)
    }

    # Need all incoming control tokens
    control_tokens = {t.edge.lookup() for t in tokens if t.edge}
    if len(incoming_controls) == 0:
        tokens_present = True
    else:
        tokens_present = len(control_tokens.intersection(incoming_controls)) == len(
            incoming_controls
        )

    if hasattr(self, "inputs"):
        required_inputs = [
            p
            for i in self.behavior.lookup().get_required_inputs()
            for p in self.input_pins(i.property_value.name)
        ]

        required_value_pins = {
            p for p in required_inputs if isinstance(p, uml.ValuePin)
        }
        # Validate values, see #120
        for pin in required_value_pins:
            if pin.value is None:
                raise ValueError(
                    f"{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}"
                )
        required_input_pins = {
            p for p in required_inputs if not isinstance(p, uml.ValuePin)
        }
        pins_with_tokens = {
            t.token_source.lookup().node.lookup() for t in tokens if not t.edge
        }
        # pin_in_edges = { i.identity: [edge for edge in self.ex.protocol.lookup().incoming_edges(i)] for i in node.inputs}

        # # Every required input pin has a token on each incoming edge
        # all([
        #     all([
        #         any([
        #             any([flow.lookup().edge == in_edge.identity
        #                  for flow in  token.token_source.lookup().incoming_flows]) # flows are into pins
        #               for token in tokens ]) # tokens going from pins to activity
        #          for in_edge in pin_in_edges[pin.identity] ])  # in_edges are going into pins
        #     for pin in required_input_pins])

        # parameter_names = {pv.parameter.lookup().property_value.name for pv in ex.parameter_values}
        # pins_with_params = {p for p in required_input_pins if p.name in parameter_names}
        # satisfied_pins = set(list(pins_with_params) + list(pins_with_tokens))
        input_pins_satisfied = required_input_pins.issubset(pins_with_tokens)
        value_pins_assigned = all({i.value for i in required_value_pins})
        if engine.permissive:
            return tokens_present
        else:
            return tokens_present and input_pins_satisfied and value_pins_assigned
    else:
        return tokens_present


uml.ActivityNode.enabled = activity_node_enabled


def activity_node_get_protocol(node: uml.ActivityNode) -> labop.Protocol:
    """Find protocol object that contains the node.

    Parameters
    ----------
    node: node in a protocol

    Returns
    -------
    protocol containing node
    """
    parent = node.get_parent()
    if isinstance(parent, labop.Protocol):
        return parent
    elif not isinstance(parent, sbol3.TopLevel):
        return parent.protocol()
    else:
        raise Exception(f"Cannot find protocol for node: {node}")


uml.ActivityNode.protocol = activity_node_get_protocol


def input_pin_enabled(
    self: uml.InputPin,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    protocol = self.protocol()
    incoming_controls = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)
    }
    incoming_objects = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)
    }

    assert len(incoming_controls) == 0  # Pins do not receive control flow

    # # Every incoming edge has a token

    tokens_present = all(
        [
            any(
                [token.edge == in_edge.identity for token in tokens]
            )  # tokens going from pins to activity
            for in_edge in incoming_objects
        ]
    )  # in_edges are going into pins

    return tokens_present or engine.permissive


uml.InputPin.enabled = input_pin_enabled


def value_pin_enabled(
    self: uml.InputPin,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    protocol = self.protocol()
    incoming_controls = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)
    }
    incoming_objects = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)
    }

    assert (
        len(incoming_controls) == 0 and len(incoming_objects) == 0
    )  # ValuePins do not receive flow

    return True


uml.ValuePin.enabled = value_pin_enabled


def output_pin_enabled(
    self: uml.InputPin,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    return False


uml.OutputPin.enabled = output_pin_enabled


def fork_node_enabled(
    self: uml.ForkNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    protocol = self.protocol()
    incoming_controls = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ControlFlow)
    }
    incoming_objects = {
        e for e in protocol.incoming_edges(self) if isinstance(e, uml.ObjectFlow)
    }

    assert (len(incoming_controls) + len(incoming_objects)) == 1 and len(
        tokens
    ) < 2  # At least one flow and no more than one token

    # Need at least one incoming control token
    tokens_present = {t.edge.lookup() for t in tokens if t.edge} == incoming_objects

    return tokens_present


uml.ForkNode.enabled = fork_node_enabled


def final_node_enabled(
    self: uml.FinalNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    """
    Check whether there exists at least one token on an incoming edge.

    Parameters
    ----------
    self : uml.FinalNode
        Node to execute
    engine : labop.ExecutionEngine
        the engine executing the node
    tokens : List[labop.ActivityEdgeFlow]
        tokens offered to node

    Returns
    -------
    bool
        is the node enabled
    """
    protocol = self.protocol()
    token_present = (
        len(
            {t.edge.lookup() for t in tokens if t.edge}.intersection(
                protocol.incoming_edges(self)
            )
        )
        > 0
    )
    return token_present


uml.FinalNode.enabled = final_node_enabled


def activity_parameter_node_enabled(
    self: uml.ActivityParameterNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    # FIXME update for permissive case where object token is not present
    return len(tokens) <= 2 and all([t.get_target() == self for t in tokens])


uml.ActivityParameterNode.enabled = activity_parameter_node_enabled


def initial_node_enabled(
    self: uml.InitialNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    return len(tokens) == 1 and tokens[0].get_target() == self


uml.InitialNode.enabled = initial_node_enabled


def merge_node_enabled(
    self: uml.MergeNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    protocol = self.protocol()
    return {t.edge.lookup() for t in tokens if t.edge} == protocol.incoming_edges(self)


uml.MergeNode.enabled = merge_node_enabled


def decision_node_enabled(
    self: uml.DecisionNode,
    engine: labop.ExecutionEngine,
    tokens: List[labop.ActivityEdgeFlow],
):
    # Cases:
    # - primary is control, input_flow, no decision_input
    # - primary is control, decision_input flow,
    # - primary is object, no decision_input
    # - primary is object, decision_input
    protocol = self.protocol()
    primary_flow = self.get_primary_incoming_flow(protocol)
    primary_token = None
    try:
        primary_token = next(t for t in tokens if t.edge.lookup() == primary_flow)
    except StopIteration:
        pass

    decision_input_token = None
    try:
        decision_input_token = next(
            t
            for t in tokens
            if isinstance(t.edge.lookup().source.lookup(), uml.OutputPin)
            and t.edge.lookup().source.lookup().get_parent().behavior
            == self.decision_input
        )
    except StopIteration:
        pass

    decision_input_flow_token = None
    try:
        decision_input_flow_token = next(
            t for t in tokens if t.edge.lookup() == self.decision_input_flow
        )
    except StopIteration:
        pass

    if isinstance(primary_flow, uml.ControlFlow):
        # Need either decision_input_flow (if no decision_input) or flow from decision_input
        if hasattr(self, "decision_input") and self.decision_input:
            # Get flow from decision_input return
            return primary_token is not None and decision_input_token is not None
        else:
            # Get flow from decision_input_flow
            return primary_token and decision_input_flow_token
    else:  # primary is an object flow
        if hasattr(self, "decision_input") and self.decision_input:
            # Get flow from decision_input return
            return decision_input_token
        else:
            # Get flow from primary
            return primary_token


uml.DecisionNode.enabled = decision_node_enabled


class ProtocolExecutionExtractor:
    def extract(self, record: labop.ActivityNodeExecution):
        pass

    def extract(self, token: labop.ActivityEdgeFlow):
        pass


class JSONProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def __init__(self) -> None:
        super().__init__()
        self.extraction_map = {
            uml.CallBehaviorAction: self.extract_call_behavior_action
        }

    def extract_call_behavior_action(self, token: labop.ActivityEdgeFlow):
        return super().extract(token)

    def extract(self, record: labop.ActivityNodeExecution):
        behavior_str = (
            record.node.lookup().behavior
            if isinstance(record.node.lookup(), uml.CallBehaviorAction)
            else (
                (
                    record.node.lookup().get_parent().behavior,
                    record.node.lookup().name,
                )
                if isinstance(record.node.lookup(), uml.Pin)
                else ""
            )
        )
        record_str = f"{record.node} ({behavior_str})"
        return record_str


class StringProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def extract(self, record: labop.ActivityNodeExecution):
        behavior_str = (
            record.node.lookup().behavior
            if isinstance(record.node.lookup(), uml.CallBehaviorAction)
            else (
                (
                    record.node.lookup().get_parent().behavior,
                    record.node.lookup().name,
                )
                if isinstance(record.node.lookup(), uml.Pin)
                else ""
            )
        )
        record_str = f"{record.node} ({behavior_str})"
        return record_str


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
        head += [extractor.extract(tail)]
        return nodes, head


labop.ProtocolExecution.backtrace = backtrace


def token_info(self: labop.ActivityEdgeFlow):
    return {
        "edge_type": (type(self.edge.lookup()) if self.edge else None),
        "source": self.token_source.lookup().node.lookup().identity,
        "target": self.get_target().identity,
        "behavior": (
            self.get_target().behavior
            if isinstance(self.get_target(), uml.CallBehaviorAction)
            else None
        ),
    }


labop.ActivityEdgeFlow.info = token_info


def protocol_execution_to_json(self):
    """
    Convert Protocol Execution to JSON
    """
    p_json = self.backtrace(extractor=JSONProtocolExecutionExtractor())[1]
    return json.dumps(p_json)


labop.ProtocolExecution.to_json = protocol_execution_to_json


def protocol_execution_unbound_inputs(self):
    unbound_input_parameters = [
        p.node.lookup().parameter.lookup().property_value
        for p in self.executions
        if isinstance(p.node.lookup(), uml.ActivityParameterNode)
        and p.node.lookup().parameter.lookup().property_value.direction
        == uml.PARAMETER_IN
        and p.node.lookup().parameter.lookup().property_value
        not in [pv.parameter.lookup().property_value for pv in self.parameter_values]
    ]
    return unbound_input_parameters


labop.ProtocolExecution.unbound_inputs = protocol_execution_unbound_inputs


def protocol_execution_unbound_outputs(self):
    unbound_output_parameters = [
        p.node.lookup().parameter.lookup().property_value
        for p in self.executions
        if isinstance(p.node.lookup(), uml.ActivityParameterNode)
        and p.node.lookup().parameter.lookup().property_value.direction
        == uml.PARAMETER_OUT
        and p.node.lookup().parameter.lookup().property_value
        not in [pv.parameter.lookup().property_value for pv in self.parameter_values]
    ]
    return unbound_output_parameters


labop.ProtocolExecution.unbound_outputs = protocol_execution_unbound_outputs


def activity_node_execute(
    self: uml.ActivityNode,
    engine: ExecutionEngine,
    node_outputs: Callable = None,
) -> List[labop.ActivityEdgeFlow]:
    """Execute a node in an activity, consuming the incoming flows and recording execution and outgoing flows

    Parameters
    ----------
    self: node to be executed
    engine: execution engine (for execution state and side-effects)

    Returns
    -------
    updated list of pending edge flows
    """
    # Extract the relevant set of incoming flow values
    inputs = [t for t in engine.tokens if self == t.get_target()]

    record = self.execute_callback(engine, inputs)
    engine.ex.executions.append(record)
    new_tokens = record.next_tokens(engine, node_outputs)

    if record:
        for specialization in engine.specializations:
            try:
                specialization.process(record, engine.ex)
            except Exception as e:
                if not engine.failsafe:
                    raise e
                l.error(
                    f"Could Not Process {record.name if record.name else record.identity}: {e}"
                )

    # return updated token list
    return new_tokens, inputs


uml.ActivityNode.execute = activity_node_execute


@abstractmethod
def activity_node_execute_callback(
    self: uml.ActivityNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    raise ValueError(
        f"Do not know how to execute node {self.identity} of type {self.type_uri}"
    )


uml.ActivityNode.execute_callback = activity_node_execute_callback


def activity_node_execution_next_tokens(
    self: labop.ActivityNodeExecution, engine: ExecutionEngine, node_outputs: Callable
) -> List[labop.ActivityEdgeFlow]:
    node = self.node.lookup()
    protocol = node.protocol()
    out_edges = [
        e
        for e in protocol.edges
        if self.node == e.source or self.node == e.source.lookup().get_parent().identity
    ]

    edge_tokens = node.next_tokens_callback(self, engine, out_edges, node_outputs)

    if edge_tokens:
        # Save tokens in the protocol execution
        engine.ex.flows += edge_tokens
    else:
        pass

    self.check_next_tokens(edge_tokens, node_outputs, engine.sample_format)

    # # Assume that unlinked output pins are possible output parameters for the protocol
    # if isinstance(self, labop.CallBehaviorExecution):
    #     output_pins = self.node.lookup().outputs
    #     unlinked_output_pins = [p for p in output_pins if p not in {e.source.lookup() for e in out_edges}]
    #     possible_output_parameter_values = [labop.ParameterValue(parameter=self.node.lookup().pin_parameter(p.name),
    #                                                             value=self.get_value())
    #                                         for p in unlinked_output_pins]
    #     engine.ex.parameter_values.extend(possible_output_parameter_values)
    return edge_tokens


labop.ActivityNodeExecution.next_tokens = activity_node_execution_next_tokens


def activity_node_execution_check_next_tokens(
    self: labop.ActivityNodeExecution,
    tokens: List[labop.ActivityEdgeFlow],
    node_outputs: Callable,
    sample_format: str,
):
    pass


labop.ActivityNodeExecution.check_next_tokens = (
    activity_node_execution_check_next_tokens
)


def call_behavior_execution_check_next_tokens(
    self: labop.CallBehaviorExecution,
    tokens: List[labop.ActivityEdgeFlow],
    node_outputs: Callable,
    sample_format: str,
):

    # ## Add the output values to the call parameter-values
    linked_parameters = []
    if not isinstance(self.node.lookup().behavior.lookup(), labop.Protocol):
        # Protocol invocation's use output values for the linkage from
        # protocol-input to subprotocol-input, so don't add as an output
        # parameter-value
        for token in tokens:
            edge = token.edge.lookup()
            if isinstance(edge, uml.ObjectFlow):
                source = edge.source.lookup()
                parameter = self.node.lookup().pin_parameter(source.name)
                linked_parameters.append(parameter)
                parameter_value = uml.literal(token.value.get_value(), reference=True)
                pv = labop.ParameterValue(parameter=parameter, value=parameter_value)
                self.call.lookup().parameter_values += [pv]

    # Assume that unlinked output pins to the parameter values of the call
    unlinked_output_parameters = [
        p
        for p in self.node.lookup().behavior.lookup().parameters
        if p.property_value.direction == uml.PARAMETER_OUT
        and p.property_value.name
        not in {lp.property_value.name for lp in linked_parameters}
    ]

    # Handle unlinked output pins by attaching them to the call
    possible_output_parameter_values = []
    for p in unlinked_output_parameters:
        value = self.get_parameter_value(p.property_value, node_outputs, sample_format)
        reference = hasattr(value, "document") and value.document is not None
        possible_output_parameter_values.append(
            labop.ParameterValue(
                parameter=p,
                value=uml.literal(value, reference=reference),
            )
        )

    self.call.lookup().parameter_values.extend(possible_output_parameter_values)

    ### Check that the same parameter names are sane:
    # 1. unbounded parameters can appear 0+ times
    # 2. unique parameters must not have duplicate values (unbounded, unique means no pair of values is the same)
    # 3. required parameters are present

    pin_sets = {}
    for pv in self.call.lookup().parameter_values:
        name = pv.parameter.lookup().property_value.name
        value = pv.value.get_value() if pv.value else None
        if name not in pin_sets:
            pin_sets[name] = []
        pin_sets[name].append(value)

    for p in self.node.lookup().behavior.lookup().parameters:
        param = p.property_value

        if (
            param.lower_value
            and param.lower_value.value > 0
            and param.name not in pin_sets
        ):
            raise ValueError(
                f"Parameter '{param.name}' is required, but does not appear as a pin"
            )

        elif param.name in pin_sets:
            count = len(pin_sets[param.name])
            unique_count = len(set(pin_sets[param.name]))
            if param.is_unique:
                if count != unique_count:
                    raise ValueError(
                        f"{param.name} has {count} values, but only {unique_count} are unique"
                    )
            if (param.lower_value and param.lower_value.value > count) or (
                param.upper_value and param.upper_value.value < count
            ):
                raise ValueError(
                    f"{param.name} has {count} values, but expecting [{param.lower_value.value}, {param.upper_value.value}] values"
                )


labop.CallBehaviorExecution.check_next_tokens = (
    call_behavior_execution_check_next_tokens
)


def activity_node_next_tokens_callback(
    self: uml.ActivityNode,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    edge_tokens = []
    for edge in out_edges:
        try:
            edge_value = source.get_value(edge, node_outputs, engine.sample_format)
        except Exception as e:
            if engine.permissive:
                edge_value = uml.literal(str(e))
            else:
                raise e

        edge_tokens.append(
            labop.ActivityEdgeFlow(
                edge=edge,
                token_source=source,
                value=edge_value,
            )
        )
    return edge_tokens


uml.ActivityNode.next_tokens_callback = activity_node_next_tokens_callback


def activity_node_execution_get_parameter_value(
    self: labop.ActivityNodeExecution,
    parameter: uml.Parameter,
    node_outputs: Callable,
    sample_format: str,
):
    if node_outputs:
        value = node_outputs(self, parameter)
    elif hasattr(self.node.lookup().behavior.lookup(), "compute_output"):
        value = self.compute_output(parameter, sample_format)
    else:
        value = f"{parameter.name}"
    return value


labop.ActivityNodeExecution.get_parameter_value = (
    activity_node_execution_get_parameter_value
)


def activity_node_execution_get_value(
    self: labop.ActivityNodeExecution,
    edge: uml.ActivityEdge,
    node_outputs: Callable,
    sample_format: str,
):
    value = ""
    node = self.node.lookup()
    reference = False

    if isinstance(edge, uml.ControlFlow):
        value = "uml.ControlFlow"
    elif isinstance(edge, uml.ObjectFlow):
        if (
            isinstance(node, uml.ActivityParameterNode)
            and node.parameter.lookup().property_value.direction == uml.PARAMETER_OUT
        ):
            parameter = node.parameter.lookup().property_value
            value = self.incoming_flows[0].lookup().value
            reference = True
        elif isinstance(node, uml.OutputPin):
            call_node = node.get_parent()
            parameter = call_node.pin_parameter(
                edge.source.lookup().name
            ).property_value
            value = self.incoming_flows[0].lookup().value
            reference = True
        else:
            parameter = node.pin_parameter(edge.source.lookup().name).property_value
            value = self.get_parameter_value(parameter, node_outputs, sample_format)
            reference = isinstance(value, sbol3.Identified) and value.identity != None

    value = uml.literal(value, reference=reference)
    return value


labop.ActivityNodeExecution.get_value = activity_node_execution_get_value


def initial_node_execute_callback(
    self: uml.InitialNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:

    non_call_edge_inputs = {
        i for i in inputs if i.edge.lookup() not in engine.ex.activity_call_edge
    }
    if len(non_call_edge_inputs) != 0:
        raise ValueError(
            f"Initial node must have zero inputs, but {self.identity} had {len(inputs)}"
        )
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)

    return record


uml.InitialNode.execute_callback = initial_node_execute_callback


def flow_final_node_execute_callback(
    self: uml.FlowFinalNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    # FlowFinalNode consumes tokens, but does not emit
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.FlowFinalNode.execute_callback = flow_final_node_execute_callback


def get_calling_behavior_execution(
    self: labop.ActivityNodeExecution,
    visited: Set[labop.ActivityNodeExecution] = None,
) -> labop.ActivityNodeExecution:
    """Look for the InitialNode for the Activity including self and identify a Calling CallBehaviorExecution (if present)

    Args:
        self (labop.ActivityNodeExecution): current search node

    Returns:
        labop.CallBehaviorExecution: CallBehaviorExecution
    """
    node = self.node.lookup()
    if visited is None:
        visited = set({})
    if isinstance(node, uml.InitialNode):
        # Check if there is a CallBehaviorExecution incoming_flow
        try:
            caller = next(
                n.lookup().token_source.lookup()
                for n in self.incoming_flows
                if isinstance(
                    n.lookup().token_source.lookup(),
                    labop.CallBehaviorExecution,
                )
            )
        except StopIteration:
            return None
        return caller
    else:
        for incoming_flow in self.incoming_flows:
            parent_activity_node = incoming_flow.lookup().token_source.lookup()
            if (
                parent_activity_node
                and (parent_activity_node not in visited)
                and parent_activity_node.node.lookup().protocol() == node.protocol()
            ):
                visited.add(parent_activity_node)
                calling_behavior_execution = (
                    parent_activity_node.get_calling_behavior_execution(visited=visited)
                )
                if calling_behavior_execution:
                    return calling_behavior_execution
        return None


labop.ActivityNodeExecution.get_calling_behavior_execution = (
    get_calling_behavior_execution
)


def final_node_execute_callback(
    self: uml.FinalNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    # FinalNode completes the activity
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.FinalNode.execute_callback = final_node_execute_callback


def call_behavior_execution_complete_subprotocol(
    self: labop.CallBehaviorExecution,
    engine: ExecutionEngine,
):
    # Map of subprotocol output parameter name to token
    subprotocol_output_tokens = {
        t.token_source.lookup().node.lookup().parameter.lookup().property_value.name: t
        for t in engine.tokens
        if isinstance(t.token_source.lookup().node.lookup(), uml.ActivityParameterNode)
        and self == t.token_source.lookup().get_calling_behavior_execution()
    }

    # Out edges of calling behavior that need tokens corresponding to the
    # subprotocol output tokens
    calling_behavior_node = self.node.lookup()

    calling_behavior_out_edges = [
        e
        for e in calling_behavior_node.protocol().edges
        if calling_behavior_node == e.source.lookup()
        or calling_behavior_node == e.source.lookup().get_parent()
    ]

    new_tokens = [
        labop.ActivityEdgeFlow(
            token_source=(
                subprotocol_output_tokens[e.source.lookup().name].token_source.lookup()
                if isinstance(e, uml.ObjectFlow)
                else self
            ),
            edge=e,
            value=(
                uml.literal(
                    subprotocol_output_tokens[e.source.lookup().name].value,
                    reference=True,
                )
                if isinstance(e, uml.ObjectFlow)
                else uml.literal("uml.ControlFlow")
            ),
        )
        for e in calling_behavior_out_edges
    ]

    # Remove output_tokens from tokens (consumed by return from subprotocol)
    engine.tokens = [
        t for t in engine.tokens if t not in subprotocol_output_tokens.values()
    ]
    engine.blocked_nodes.remove(self)

    return new_tokens


labop.CallBehaviorExecution.complete_subprotocol = (
    call_behavior_execution_complete_subprotocol
)


def final_node_next_tokens_callback(
    self: uml.FinalNode,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    calling_behavior_execution = source.get_calling_behavior_execution()
    if calling_behavior_execution:
        new_tokens = calling_behavior_execution.complete_subprotocol(engine)
        return new_tokens
    else:
        return []


uml.FinalNode.next_tokens_callback = final_node_next_tokens_callback


def fork_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    if len(inputs) != 1:
        raise ValueError(
            f"Fork node must have precisely one input, but {self.identity} had {len(inputs)}"
        )
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.ForkNode.execute_callback = fork_node_execute_callback


def fork_node_next_tokens_callback(
    self: uml.ForkNode,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    [incoming_flow] = source.incoming_flows
    incoming_value = incoming_flow.lookup().value
    edge_tokens = [
        labop.ActivityEdgeFlow(
            edge=edge,
            token_source=source,
            value=uml.literal(incoming_value, reference=True),
        )
        for edge in out_edges
    ]
    return edge_tokens


uml.ForkNode.next_tokens_callback = fork_node_next_tokens_callback


def control_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.ControlNode.execute_callback = control_node_execute_callback


def fork_node_execute_callback(
    self: uml.ForkNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    if len(inputs) != 1:
        raise ValueError(
            f"Fork node must have precisely one input, but {self.identity} had {len(inputs)}"
        )
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.ForkNode.execute_callback = fork_node_execute_callback


def decision_node_next_tokens_callback(
    self: uml.DecisionNode,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    try:
        decision_input_flow_token = next(
            t
            for t in source.incoming_flows
            if t.lookup().edge == self.decision_input_flow
        ).lookup()
        decision_input_flow = decision_input_flow_token.edge.lookup()
        decision_input_value = decision_input_flow_token.value
    except StopIteration as e:
        decision_input_flow_token = None
        decision_input_value = None
        decision_input_flow = None
    try:
        decision_input_return_token = next(
            t
            for t in source.incoming_flows
            if isinstance(t.lookup().edge.lookup().source.lookup(), uml.OutputPin)
            and t.lookup().token_source.lookup().node.lookup().behavior
            == self.decision_input
        ).lookup()
        decision_input_return_flow = decision_input_return_token.edge.lookup()
        decision_input_return_value = decision_input_return_token.value
    except StopIteration as e:
        decision_input_return_token = None
        decision_input_return_value = None
        decision_input_return_flow = None

    try:
        primary_input_flow_token = next(
            t
            for t in source.incoming_flows
            if t.lookup() != decision_input_flow_token
            and t.lookup() != decision_input_return_token
        ).lookup()
        primary_input_flow = primary_input_flow_token.edge.lookup()
        primary_input_value = primary_input_flow_token.value
    except StopIteration as e:
        primary_input_value = None

    # Cases to evaluate guards of decision node:
    # 1. primary_input_flow is ObjectFlow, no decision_input, no decision_input_flow:
    #    Use primary_input_flow token to decide if guard is satisfied
    # 2. primary_input_flow is any, no decision_input, decision_input_flow present:
    #    Use decision_input_flow token to decide if guard is satisfied

    # 3. primary_input_flow is ControlFlow, decision_input present, no decision_input_flow:
    #    Use decision_input return value to decide if guard is satisfied (decision_input has no params)
    # 4. primary_input_flow is ControlFlow, decision_input present, decision_input_flow present:
    #    Use decision_input return value to decide if guard is satisfied (decision_input has decision_input_flow supplied parameter)

    # 5. primary_input_flow is ObjectFlow, decision_input present, no decision_input_flow:
    #    Use decision_input return value to decide if guard is satisfied (decision_input has primary_input_flow supplied parameter)
    # 6. primary_input_flow is ObjectFlow, decision_input present,  decision_input_flow present:
    #    Use decision_input return value to decide if guard is satisfied (decision_input has primary_input_flow and decision_input_flow supplied parameters)

    try:
        else_edge = next(
            edge for edge in out_edges if edge.guard.value == uml.DECISION_ELSE
        )
    except StopIteration as e:
        else_edge = None
    non_else_edges = [edge for edge in out_edges if edge != else_edge]

    def satisfy_guard(value, guard):
        if (value is None) or isinstance(value, uml.LiteralNull):
            return (guard is None) or isinstance(guard, uml.LiteralNull)
        elif (guard is None) or isinstance(guard, uml.LiteralNull):
            return False
        else:
            if isinstance(value.value, str):
                return value.value == str(guard.value)
            else:
                return value.value == guard.value

    if hasattr(self, "decision_input") and self.decision_input:
        # Cases: 3, 4, 5, 6
        # The cases are combined because the cases refer to the inputs of the decision_input behavior
        # use decision_input_value to eval guards

        active_edges = [
            edge
            for edge in non_else_edges
            if satisfy_guard(decision_input_return_value, edge.guard)
        ]
    else:
        # Cases: 1, 2
        if decision_input_flow:
            # Case 2
            # use decision_input_flow_token to eval guards

            active_edges = [
                edge
                for edge in non_else_edges
                if satisfy_guard(decision_input_flow_token.value, edge.guard)
            ]

        elif primary_input_flow and isinstance(primary_input_flow, uml.ObjectFlow):
            # Case 1
            # use primary_input_flow_token to eval guards
            # Outgoing tokens are uml.ObjectFlow

            active_edges = [
                edge
                for edge in non_else_edges
                if satisfy_guard(primary_input_flow_token.value, edge.guard)
            ]
        else:
            raise Exception(
                "ERROR: Cannot evaluate DecisionNode with no decision_input, no decision_input_flow, and a None or uml.ControlFlow primary_input"
            )

    assert else_edge or len(active_edges) > 0

    if len(active_edges) > 0:
        # FIXME always take first active edge, but could be different.
        active_edge = active_edges[0]
    else:
        active_edge = else_edge

    # Pick the value of the incoming_flow that corresponds to the primary_incoming edge
    edge_tokens = [
        labop.ActivityEdgeFlow(
            edge=active_edge,
            token_source=source,
            value=uml.literal(primary_input_value),
        )
    ]
    return edge_tokens


uml.DecisionNode.next_tokens_callback = decision_node_next_tokens_callback


def activity_parameter_node_execute_callback(
    self: uml.ActivityParameterNode,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    if self.parameter.lookup().property_value.direction == uml.PARAMETER_OUT:
        try:
            values = [
                i.value.get_value()
                for i in inputs
                if isinstance(i.edge.lookup(), uml.ObjectFlow)
            ]
            if len(values) == 1:
                value = uml.literal(values[0], reference=True)
            elif len(values) == 0:
                value = uml.literal(self.parameter.lookup().property_value.name)
            engine.ex.parameter_values += [
                labop.ParameterValue(
                    parameter=self.parameter.lookup(),
                    value=value,
                )
            ]
        except Exception as e:
            if not engine.permissive:
                raise ValueError(
                    f"ActivityParameterNode execution for {self.identity} does not have an ObjectFlow token input present."
                )
    return record


uml.ActivityParameterNode.execute_callback = activity_parameter_node_execute_callback


def activity_parameter_node_next_tokens_callback(
    self: uml.ActivityParameterNode,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    if self.parameter.lookup().property_value.direction == uml.PARAMETER_IN:
        try:
            parameter_value = next(
                pv.value
                for pv in engine.ex.parameter_values
                if pv.parameter == self.parameter
            )
        except StopIteration as e:
            try:
                parameter_value = self.parameter.lookup().property_value.default_value
            except Exception as e:
                raise Exception(
                    f"ERROR: Could not find input parameter {self.parameter.lookup().property_value.name} value and/or no default_value."
                )
        edge_tokens = [
            labop.ActivityEdgeFlow(
                edge=edge,
                token_source=source,
                value=uml.literal(value=parameter_value, reference=True),
            )
            for edge in out_edges
        ]
    else:
        calling_behavior_execution = source.get_calling_behavior_execution()
        if calling_behavior_execution:
            return_edge = uml.ObjectFlow(
                source=self,
                target=calling_behavior_execution.node.lookup().output_pin(
                    self.parameter.lookup().property_value.name
                ),
            )
            engine.ex.activity_call_edge += [return_edge]
            edge_tokens = [
                labop.ActivityEdgeFlow(
                    edge=return_edge,
                    token_source=source,
                    value=source.get_value(
                        return_edge, node_outputs, engine.sample_format
                    )
                    # uml.literal(source.incoming_flows[0].lookup().value)
                )
            ]
        else:
            edge_tokens = []
    return edge_tokens


uml.ActivityParameterNode.next_tokens_callback = (
    activity_parameter_node_next_tokens_callback
)


def call_behavior_action_execute_callback(
    self: uml.CallBehaviorAction,
    engine: ExecutionEngine,
    inputs: List[labop.ActivityEdgeFlow],
) -> labop.ActivityNodeExecution:
    record = labop.CallBehaviorExecution(node=self, incoming_flows=inputs)
    completed_normally = True
    # Get the parameter values from input tokens for input pins
    input_pin_values = {
        token.token_source.lookup().node.lookup().identity: []
        for token in inputs
        if not token.edge
    }
    for token in inputs:
        if not token.edge:
            name = token.token_source.lookup().node.lookup().identity
            input_pin_values[name].append(uml.literal(token.value, reference=True))

    # Get Input value pins
    value_pin_values = {}

    # Validate Pin values, see #130
    # Although enabled_activity_node method also validates Pin values,
    # it only checks required Pins.  This check is necessary to check optional Pins.
    required_inputs = [
        p
        for i in self.behavior.lookup().get_required_inputs()
        for p in self.input_pins(i.property_value.name)
    ]
    for pin in [i for i in self.inputs if i.identity not in input_pin_values]:
        value = pin.value if hasattr(pin, "value") else None
        if value is None:
            if pin in required_inputs:
                completed_normally = False
                if engine.permissive:
                    engine.issues[engine.ex.display_id].append(
                        ExecutionError(
                            f"{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}"
                        )
                    )
                    value = uml.literal("Error")
                else:
                    raise ValueError(
                        f"{self.behavior.lookup().display_id} Action has no ValueSpecification for Pin {pin.name}"
                    )
        value_pin_values[pin.identity] = value
        # Check that pin corresponds to an input parameter.  Will cause Exception if does not exist.
        parameter = self.pin_parameter(pin.name)

    # Convert References
    value_pin_values = {
        k: [uml.literal(value=v.get_value(), reference=True)]
        for k, v in value_pin_values.items()
        if v is not None
    }
    pin_values = {**input_pin_values, **value_pin_values}  # merge the dicts

    parameter_values = [
        labop.ParameterValue(
            parameter=self.pin_parameter(pin.name),
            value=value,
        )
        for pin in self.inputs
        for value in (pin_values[pin.identity] if pin.identity in pin_values else [])
    ]
    # parameter_values.sort(
    #     key=lambda x: engine.ex.document.find(x.parameter).index
    # )
    call = labop.BehaviorExecution(
        f"execute_{engine.next_id()}",
        parameter_values=parameter_values,
        completed_normally=True,
        start_time=engine.get_current_time(),  # TODO: remove str wrapper after sbol_factory #22 fixed
        end_time=engine.get_current_time(),  # TODO: remove str wrapper after sbol_factory #22 fixed
        consumed_material=[],
    )  # FIXME handle materials
    record.call = call

    engine.ex.document.add(call)

    return record


uml.CallBehaviorAction.execute_callback = call_behavior_action_execute_callback


def call_behavior_action_next_tokens_callback(
    self: uml.CallBehaviorAction,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    if isinstance(self.behavior.lookup(), labop.Protocol):
        if engine.is_asynchronous:
            # Push record onto blocked nodes to complete
            engine.blocked_nodes.add(source)
            # new_tokens are those corresponding to the subprotocol initiating_nodes
            init_nodes = self.behavior.lookup().initiating_nodes()

            def get_invocation_edge(r, n):
                invocation = {}
                value = None
                if isinstance(n, uml.InitialNode):
                    try:
                        invocation["edge"] = uml.ControlFlow(source=r.node, target=n)
                        engine.ex.activity_call_edge += [invocation["edge"]]
                        source = next(
                            i
                            for i in r.incoming_flows
                            if hasattr(i.lookup(), "edge")
                            and i.lookup().edge
                            and isinstance(i.lookup().edge.lookup(), uml.ControlFlow)
                        )
                        invocation["value"] = uml.literal(
                            source.lookup().value, reference=True
                        )

                    except StopIteration as e:
                        pass

                elif isinstance(n, uml.ActivityParameterNode):
                    # if ActivityParameterNode is a ValuePin of the calling behavior, then it won't be an incoming flow
                    source = self.input_pin(n.parameter.lookup().property_value.name)
                    invocation["edge"] = uml.ObjectFlow(source=source, target=n)
                    engine.ex.activity_call_edge += [invocation["edge"]]
                    # ex.protocol.lookup().edges.append(invocation['edge'])
                    if isinstance(source, uml.ValuePin):
                        invocation["value"] = uml.literal(source.value, reference=True)
                    else:
                        try:
                            source = next(
                                iter(
                                    [
                                        i
                                        for i in r.incoming_flows
                                        if i.lookup()
                                        .token_source.lookup()
                                        .node.lookup()
                                        .name
                                        == n.parameter.lookup().property_value.name
                                    ]
                                )
                            )
                            # invocation['edge'] = uml.ObjectFlow(source=source.lookup().token_source.lookup().node.lookup(), target=n)
                            # engine.ex.activity_call_edge += [invocation['edge']]
                            # ex.protocol.lookup().edges.append(invocation['edge'])
                            invocation["value"] = uml.literal(
                                source.lookup().value, reference=True
                            )
                        except StopIteration as e:
                            pass

                return invocation

            new_tokens = [
                labop.ActivityEdgeFlow(
                    token_source=source,
                    **get_invocation_edge(source, init_node),
                )
                for init_node in init_nodes
            ]
            # engine.ex.flows += new_tokens

            if len(new_tokens) == 0:
                # Subprotocol does not have a body, so need to complete the CallBehaviorAction here, otherwise would have seen a FinalNode.
                new_tokens = source.complete_subprotocol(engine)

        else:  # is synchronous execution
            # Execute subprotocol
            self.execute(
                self.behavior.lookup(),
                engine.ex.association[0].agent.lookup(),
                id=f"{engine.display_id}{uuid.uuid4()}".replace("-", "_"),
                parameter_values=[],
            )
    else:
        new_tokens = uml.ActivityNode.next_tokens_callback(
            self, source, engine, out_edges, node_outputs
        )

    return new_tokens


uml.CallBehaviorAction.next_tokens_callback = call_behavior_action_next_tokens_callback


def pin_execute_callback(
    self: uml.Pin, engine: ExecutionEngine, inputs: List[labop.ActivityEdgeFlow]
) -> labop.ActivityNodeExecution:
    record = labop.ActivityNodeExecution(node=self, incoming_flows=inputs)
    return record


uml.Pin.execute_callback = pin_execute_callback


def input_pin_next_tokens_callback(
    self: uml.InputPin,
    source: labop.ActivityNodeExecution,
    engine: ExecutionEngine,
    out_edges: List[uml.ActivityEdge],
    node_outputs: Callable,
) -> List[labop.ActivityEdgeFlow]:
    assert len(source.incoming_flows) == len(
        engine.ex.protocol.lookup().incoming_edges(source.node.lookup())
    )
    incoming_flows = [f.lookup() for f in source.incoming_flows]
    pin_values = [
        uml.literal(value=incoming_flow.value, reference=True)
        for incoming_flow in incoming_flows
    ]
    edge_tokens = [
        labop.ActivityEdgeFlow(edge=None, token_source=source, value=pin_value)
        for pin_value in pin_values
    ]
    return edge_tokens


uml.InputPin.next_tokens_callback = input_pin_next_tokens_callback


def activity_node_execution_get_token_source(
    self: labop.ActivityNodeExecution,
    parameter: uml.Parameter,
    target: labop.ActivityNodeExecution = None,
) -> labop.CallBehaviorExecution:
    # Get a ActivityNodeExecution that produced this token assigned to this ActivityNodeExecution parameter.
    # The immediate predecessor will be the token_source

    node = self.node.lookup()
    print(self.identity + " " + node.identity + " param = " + str(parameter))
    if (
        isinstance(node, uml.InputPin)
        or isinstance(node, uml.ForkNode)
        or isinstance(node, uml.CallBehaviorAction)
    ):
        main_target = target if target else self
        for flow in self.incoming_flows:
            source = flow.lookup().get_token_source(parameter, target=main_target)
            if source:
                return source
        return None
    else:
        return self

    node = self.node.lookup()
    print(self.identity + " " + node.identity + " param = " + str(parameter))
    if (
        isinstance(node, uml.InputPin)
        or isinstance(node, uml.ForkNode)
        or isinstance(node, uml.CallBehaviorAction)
    ):
        main_target = target if target else self
        for flow in self.incoming_flows:
            source = flow.lookup().get_token_source(parameter, target=main_target)
            if source:
                return source
        return None
    else:
        return self


labop.ActivityNodeExecution.get_token_source = activity_node_execution_get_token_source


def call_behavior_execution_get_token_source(
    self: labop.CallBehaviorExecution,
    parameter: uml.Parameter,
    target: labop.ActivityNodeExecution = None,
) -> labop.CallBehaviorExecution:
    node = self.node.lookup()
    print(self.identity + " " + node.identity + " param = " + str(parameter))
    if parameter:
        return labop.ActivityNodeExecution.get_token_source(
            self, parameter, target=target
        )
    else:
        return self


labop.CallBehaviorExecution.get_token_source = call_behavior_execution_get_token_source


def activity_edge_flow_get_token_source(
    self: labop.ActivityEdgeFlow,
    parameter: uml.Parameter,
    target: labop.ActivityNodeExecution = None,
) -> labop.CallBehaviorExecution:
    node = self.token_source.lookup().node.lookup()
    print(self.identity + " src = " + node.identity + " param = " + str(parameter))
    if parameter and isinstance(node, uml.InputPin):
        if node == target.node.lookup().input_pin(parameter.name):
            return self.token_source.lookup().get_token_source(None, target=target)
        else:
            return None
    elif not parameter:
        return self.token_source.lookup().get_token_source(None, target=target)
    else:
        return None


labop.ActivityEdgeFlow.get_token_source = activity_edge_flow_get_token_source
