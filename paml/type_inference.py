import paml
from paml.lib.library_type_inference import primitive_type_inference_functions

##############################
# Class for carrying a typing process


class ProtocolTyping:
    def __init__(self, protocol: paml.Protocol):
        self.flow_values = {}  # dictionary of paml.Flow : type value, includes subprotocols too
        self.typed_protocols = set()  # protocol and subprotocols already evaluated or in process of evaluation
        # actually trigger the inference
        self.infer_typing(protocol)

    def infer_typing(self, protocol : paml.Protocol):
        self.typed_protocols.add(protocol)
        pending_activities = set(protocol.activities)
        while pending_activities:
            non_blocked = {a for a in pending_activities if self.inflows_satisfied(a)}
            if not non_blocked:
                raise ValueError("Could not infer all flow types: circular dependency?")
            for activity in non_blocked:
                activity.infer_typing(self)
            pending_activities -= non_blocked

    def inflows_satisfied(self, activity):
        unsatisfied = {flow for flow in activity.input_flows() if flow not in self.flow_values.keys()}
        return len(unsatisfied) == 0


#############################
# Inference utilities

def pin_input_type(self, typing: ProtocolTyping):
    try:
        return self.value
    except AttributeError:
        in_flows = self.input_flows()
        assert len(in_flows) == 1, \
            ValueError("Expected one input flow for '" + self.get_parent().identity + "' but found " + len(in_flows))
        return typing.flow_values[in_flows.pop()]
paml.Pin.input_type = pin_input_type


def pin_assert_output_type(self, typing: ProtocolTyping, value):
    out_flows = self.output_flows()
    assert len(out_flows) == 1, \
        ValueError("Expected one output flow for '" + self.get_parent().identity + "' but found " + len(out_flows))
    typing.flow_values[out_flows.pop()] = value
paml.Pin.assert_output_type = pin_assert_output_type


#############################
# Inference over Activities
def initial_infer_typing(self, typing: ProtocolTyping):
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
paml.Initial.infer_typing = initial_infer_typing


def final_infer_typing(self, _: ProtocolTyping):
    assert len(self.direct_output_flows()) == 0  # should be no outputs
paml.Final.infer_typing = final_infer_typing


def fork_decision_infer_typing(self, typing: ProtocolTyping):
    assert len(direct_inflows) == 1  # should be precisely one input
    in_type = flow_values[next(self.direct_input_flows)]
    typing.flow_values.update({f: in_type for f in self.direct_output_flows()})
paml.Fork.infer_typing = fork_decision_infer_typing
paml.Decision.infer_typing = fork_decision_infer_typing


def join_infer_typing(self, typing: ProtocolTyping):
    assert len(self.direct_output_flows()) == 1  # should be precisely one output
    typing.flow_values[self.direct_output_flows().pop()] = \
        join_values({typing.flow_values[f] for f in self.direct_input_flows()})
paml.Join.infer_typing = join_infer_typing

# TODO: add type inference for Merge


def primitiveexecutable_infer_typing(self, typing: ProtocolTyping):
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
    inference_function = primitive_type_inference_functions[self.instance_of.lookup().identity]
    inference_function(self, typing)
paml.PrimitiveExecutable.infer_typing = primitiveexecutable_infer_typing

# TODO: add type inference for SubProtocol
def subprotocol_infer_typing(self: paml.SubProtocol, typing: ProtocolTyping):
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
    subprotocol = self.instance_of.lookup()
    if subprotocol not in typing.typed_protocols():
        # add types for inputs
        input_pin_flows = self.input_flows() - self.direct_input_flows()
        typing.flow_values.update({subprotocol.input_value(f.sink).direct_input_flows(): typing.flow_values[f] for f in input_pin_flows})
        # run the actual inference
        typing.infer_typing(subprotocol)
    # pull values from outputs' inferred values
    output_pin_flows = self.output_flows() - self.direct_output_flows()
    typing.flow_values.update({f:typing.flow_values[subprotocol.output_value(f.sink).direct_output_flows()] for f in output_pin_flows})
paml.SubProtocol.infer_typing = subprotocol_infer_typing


def value_infer_typing(self, typing: ProtocolTyping):
    assert len(self.direct_output_flows()) == 1  # should be precisely one output
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
paml.Value.infer_typing = value_infer_typing



#################
# Join is a kludge for now
# TODO: Make a more principled approach to inference of Join, which will also provide an architcture for Merge
def join_locations(value_set):
    if not value_set:
        return paml.HeterogeneousSamples()
    next_value = value_set.pop()
    rest = join_locations(value_set)
    if isinstance(next_value, paml.ReplicateSamples):
        rest.replicate_samples.append(next_value)
    elif isinstance(next_value, paml.HeterogeneousSamples):
        for x in next_value.replicate_samples:
            rest.replicate_samples.append(x)
    else:
        raise ValueError("Don't know how to join locations for "+str(value_set))
    return rest

def join_values(value_set):
    if all(isinstance(x,paml.LocatedSamples) for x in value_set):
        return join_locations(value_set)
    # if we fall through to the end, then we didn't know how to infer
    raise ValueError("Don't know how to join values types for "+str(value_set))




