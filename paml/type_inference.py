import paml
import sbol3

##############################
# Visitors for computing flow types
def type_from_pin_or_flow(executable, pin_name, flow_values):
    pin = executable.input_pin(pin_name)
    if isinstance(pin, paml.LocalValuePin) or isinstance(pin, paml.ReferenceValuePin) or isinstance(pin, paml.SimpleValuePin):
        return pin.value
    else:
        return flow_values[pin.input_flow()]

def inference_provision(executable, flow_values):
    resource = type_from_pin_or_flow(executable, 'resource', flow_values)
    location = type_from_pin_or_flow(executable, 'destination', flow_values)
    samples = paml.ReplicateSamples()
    samples.in_location.append(location)
    samples.specification = resource
    samples_flow = executable.output_pin('samples').output_flow()
    return {samples_flow : samples}

def inference_absorbance(executable, flow_values):
    samples = type_from_pin_or_flow(executable, 'samples', flow_values)
    # TODO: make this a LocatedData rather than just copying the samples
    # samples = paml.LocatedData()
    samples_flow = executable.output_pin('measurements').output_flow()
    return {samples_flow : samples}

primitive_inference = {
    'https://bioprotocols.org/paml/primitives/liquid_handling/Provision' : inference_provision,
    'https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance' : inference_absorbance
}

def primitive_types(activity, flow_values):
    inference_function = primitive_inference[activity.instance_of.lookup().identity]
    assert inference_function
    return inference_function(activity, flow_values)

def inflows_satisfied(protocol,flow_values,activity):
    inflows = {x for x in protocol.flows if (x.sink.lookup() == activity) or (isinstance(activity,paml.Executable) and x.sink.lookup() in activity.input)}
    unsatisfied = inflows - flow_values.keys()
    return len(unsatisfied) == 0

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

# returns a dictionary of outflow to type
def outflow_types(protocol,activity,flow_values):
    direct_outflows = {x for x in protocol.flows if (x.source.lookup() == activity)}
    direct_inflows = {x for x in protocol.flows if (x.sink.lookup() == activity)}
    if isinstance(activity, paml.Control):
        if isinstance(activity, paml.Initial):
            return {x: None for x in direct_outflows}
        elif isinstance(activity, paml.Final):
            assert len(direct_outflows)==0 # should be no outputs
            return {}
        elif isinstance(activity, paml.Fork) or isinstance(activity, paml.Decision):
            assert len(direct_inflows)==1 # should be precisely one input
            in_type = flow_values[next(direct_inflows)]
            return {x: in_type for x in direct_outflows}
        elif isinstance(activity, paml.Join):
            assert len(direct_outflows)==1 # should be precisely one output
            return {direct_outflows.pop() : join_values({flow_values[x] for x in direct_inflows})}
    elif isinstance(activity, paml.PrimitiveExecutable):
        direct_types = {x:None for x in direct_outflows}
        pin_types = primitive_types(activity, flow_values)
        return direct_types | pin_types
    elif isinstance(activity, paml.Value):
        assert len(direct_outflows) == 1  # should be precisely one output
        return {x: None for x in direct_outflows}
    # if we fall through to the end, then we didn't know how to infer
    raise ValueError("Don't know how to infer outflow types for "+str(activity))


##############################
# Infer values carried on flows

flow_values = {} # dictionary of flow : type mappings
def infer_flow_values(protocol:paml.Protocol):
    pending_activities = set(protocol.activities)
    while pending_activities:
        non_blocked = {x for x in pending_activities if inflows_satisfied(protocol, flow_values, x)}
        if not non_blocked:
            raise ValueError("Could not infer all flow types: circular dependency?")
            break
        for activity in non_blocked:
            flow_values.update(outflow_types(protocol, activity, flow_values))
        pending_activities -= non_blocked
    return flow_values # TODO: remove kludge, put the values into the data model

