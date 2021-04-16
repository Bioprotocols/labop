import paml
import sbol3

##############################
# Class for carrying a typing process


class ProtocolTyping:
    primitive_type_inference = {}  # dictionary of identity : function for typing primitives


    def __init__(self, protocol: paml.Protocol):
        self.flow_values = {}  # dictionary of paml.Flow : type value
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
        assert len(in_flows) == 1, ValueError("Expected one input flow for '" + self.get_parent().identity + "' but found " + len(in_flows))
        return typing.flow_values[in_flows.pop()]
paml.Pin.input_type = pin_input_type

def pin_assert_output_type(self, typing: ProtocolTyping, value):
    out_flows = self.output_flows()
    assert len(out_flows) == 1, ValueError("Expected precisely one output flow for '" + self.get_parent().identity + "' but found " + len(out_flows))
    typing.flow_values[out_flows.pop()] = value
paml.Pin.assert_output_type = pin_assert_output_type


#############################
# Inference over Activities
def initial_infer_typing(self, typing: ProtocolTyping):
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
paml.Initial.infer_typing = initial_infer_typing

def final_infer_typing(self, typing: ProtocolTyping):
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
    typing.flow_values[self.direct_output_flows().pop()] = join_values({typing.flow_values[f] for f in self.direct_input_flows()})
paml.Join.infer_typing = join_infer_typing

def primitiveexecutable_infer_typing(self, typing: ProtocolTyping):
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
    inference_function = typing.primitive_type_inference[self.instance_of.lookup().identity]
    inference_function(self, typing)
paml.PrimitiveExecutable.infer_typing = primitiveexecutable_infer_typing

def value_infer_typing(self, typing: ProtocolTyping):
    assert len(self.direct_output_flows()) == 1  # should be precisely one output
    typing.flow_values.update({f: None for f in self.direct_output_flows()})
paml.Value.infer_typing = value_infer_typing

#############################
# Primitives TBD

def liquid_handling_Provision_infer_typing(executable, typing: ProtocolTyping):
    resource = executable.input_pin('resource').input_type(typing)
    location = executable.input_pin('destination').input_type(typing)
    samples = paml.ReplicateSamples(specification = resource)
    samples.in_location.append(location)
    executable.output_pin('samples').assert_output_type(typing, samples)
ProtocolTyping.primitive_type_inference['https://bioprotocols.org/paml/primitives/liquid_handling/Provision'] = liquid_handling_Provision_infer_typing

def spectrophotometry_MeasureAbsorbance_infer_typing(executable, typing: ProtocolTyping):
    samples = executable.input_pin('samples').input_type(typing)
    # TODO: make this a LocatedData rather than just copying the samples
    # samples = paml.LocatedData()
    executable.output_pin('measurements').assert_output_type(typing, samples)
ProtocolTyping.primitive_type_inference['https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance'] = spectrophotometry_MeasureAbsorbance_infer_typing


# kludge for now
def join_locations(value_set):
    if not value_set:
        return paml.HeterogeneousSamples()
    next = value_set.pop()
    rest = join_locations(value_set)
    if isinstance(next, paml.ReplicateSamples):
        rest.replicate_samples.append(next)
    elif isinstance(next, paml.HeterogeneousSamples):
        for x in next.replicate_samples: rest.replicate_samples.append(x)
    else:
        raise ValueError("Don't know how to join locations for "+str(value_set))
    return rest

def join_values(value_set):
    if all(isinstance(x,paml.LocatedSamples) for x in value_set):
        return join_locations(value_set)
    # if we fall through to the end, then we didn't know how to infer
    raise ValueError("Don't know how to join values types for "+str(value_set))



