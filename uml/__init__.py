from sbol_factory import SBOLFactory, UMLFactory
import os
import posixpath

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)), 'uml.ttl'),
                          'http://bioprotocols.org/uml#')
__umlfactory__ = UMLFactory(__factory__)

###########################################
# Define extension methods for ValueSpecification


def literal(value):
    """Construct a UML LiteralSpecification based on the value of the literal passed

    Note: if you need a reference rather than composition of a child object, that should be done by constructing
    LiteralReference directly
    :param value: the value to embed as a literal
    :return: LiteralSpecification of the appropriate type for the value
    """
    if value is None:
        return LiteralNull()
    elif isinstance(value, str):
        return LiteralString(value=value)
    elif isinstance(value, int):
        return LiteralInteger(value=value)
    elif isinstance(value, bool):
        return LiteralBoolean(value=value)
    elif isinstance(value, float):
        return LiteralReal(value=value)
    elif isinstance(value, sbol3.TopLevel):
        return LiteralReference(value=value)
    elif isinstance(value, sbol3.Identified):
        return LiteralIdentified(value=value)
    else:
        raise ValueError(f'Don\'t know how to make literal from {type(value)} "{value}"')


###########################################
# Define extension methods for Behavior

def behavior_add_parameter(self, name: str, param_type: str, direction: str, optional: boolean = False):
    """Add a Parameter for this Behavior; usually not called directly

    Note: Current assumption is that cardinality is either [0..1] or 1
    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :param direction: should be 'in' or 'out'
    :param optional: True if the Parameter is optional; default is False
    :return: Parameter that has been added
    """
    param = Parameter(name=name, type=param_type, direction=direction, isOrdered=True, isUnique=True)
    param.upperValue = literal(1)  # all parameters are assumed to have cardinality [0..1] or 1 for now
    if optional:
        param.lowerValue = literal(0)
    else:
        param.lowerValue = literal(1)
    self.parameters.append(param)
    return param
Behavior.add_parameter = behavior_add_parameter  # Add to class via monkey patch


def behavior_add_input(self, name: str, param_type: str, optional=False):
    """Add an input Parameter for this Behavior

    Note: Current assumption is that cardinality is either [0..1] or 1

    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :param optional: True if the Parameter is optional; default is False
    :return: Parameter that has been added
    """
    return self.add_parameter(name, param_type, 'in', optional)
Behavior.add_input = behavior_add_input  # Add to class via monkey patch


def behavior_add_output(self, name, param_type):
    """Add an output Parameter for this Behavior

    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :return: Parameter that has been added
    """
    return self.add_parameter(name, param_type, 'out')
Behavior.add_output = behavior_add_output  # Add to class via monkey patch


###########################################
# Define extension methods for CallBehaviorAction

def call_behavior_action_input_pin(self, pin_name: str):
    """Find an input pin on the action with the specified name

    :param pin_name:
    :return: Pin with specified name
    """
    pin_set = {x for x in self.inputs if x.name == pin_name}
    if len(pin_set) == 0:
        raise ValueError(f'Could not find input pin named {pin_name}')
    if len(pin_set) > 1:
        raise ValueError(f'Found more than one input pin named {pin_name}')
    return pin_set.pop()
CallBehaviorAction.input_pin = call_behavior_action_input_pin  # Add to class via monkey patch


def call_behavior_action_output_pin(self, pin_name: str):
    """Find an output pin on the action with the specified name

    :param pin_name:
    :return: Pin with specified name
    """
    pin_set = {x for x in self.outputs if x.name == pin_name}
    if len(pin_set) == 0:
        raise ValueError(f'Could not find output pin named {pin_name}')
    if len(pin_set) > 1:
        raise ValueError(f'Found more than one output pin named {pin_name}')
    return pin_set.pop()
CallBehaviorAction.output_pin = call_behavior_action_output_pin  # Add to class via monkey patch


def make_call_behavior_action(behavior: Behavior, **input_pin_literals):
    """Create a call to a Behavior (but doesn't add it anywhere)

    :param behavior: Behavior to be called
    :param input_pin_literals: map of literal values to be assigned to specific pins
    :return: newly constructed
    """
    # first, make sure that all of the keyword arguments are in the inputs of the behavior
    unmatched_keys = [key for key in input_pin_literals.keys() if key not in (i.name for i in behavior.inputs)]
    if unmatched_keys:
        raise ValueError(f'Specification for "{behavior.display_id}" does not have inputs: {unmatched_keys}')

    # create action
    action = CallBehaviorAction(behavior=behavior)

    # Instantiate input pins
    for parameter in behavior.inputs:
        if parameter.name in input_pin_literals:
            value = input_pin_literals[parameter.name]
            # TODO: type check relationship between value and parameter type specification
            action.inputs.append(ValuePin(name=parameter.name, type=parameter.type, value=literal(value)))
        else:  # if not a constant, then just a generic InputPin
            action.inputs.append(InputPin(name=parameter.name, type=parameter.type))

    # Instantiate output pins
    for parameter in behavior.outputs:
        action.outputs.append(OutputPin(name=parameter.name, type=parameter.type))

    return action


###########################################
# Define extension methods for Activity

def activity_initial(self):
    """Find or create an initial node in an Activity.

    Note that while UML allows multiple initial nodes, use of this routine assumes a single one is sufficient.
    :return: InitialNode for Activity
    """

    initial = [a for a in self.activities if isinstance(a, InitialNode)]
    if not initial:
        self.activities.append(InitialNode())
        return self.initial()
    elif len(initial) == 1:
        return initial[0]
    else:
        raise ValueError(f'Activity "{self.display_id}" assumed to have one initial node, but found {len(initial)}')
# Monkey patch:
Activity.initial = activity_initial  # Add to class via monkey patch


def activity_final(self):
    """Find or create a final node in a Activity

    Note that while UML allows multiple final nodes, use of this routine assumes a single is sufficient.
    :return: FinalNode for Activity
    """
    final = [a for a in self.activities if isinstance(a, FinalNode)]
    if not final:
        self.activities.append(FlowFinalNode())
        return self.final()
    elif len(final) == 1:
        return final[0]
    else:
        raise ValueError(f'Activity "{self.display_id}" assumed to have one initial node, but found {len(initial)}')
# Monkey patch:
Activity.final = activity_final  # Add to class via monkey patch


def activity_call_behavior(self, behavior: Behavior, **input_pin_map):
    """Call a Behavior as an Action in an Activity

    :param behavior: Activity to be invoked (object or name)
    :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
    :return: CallBehaviorAction that invokes the Behavior
    """

    # Any ActivityNode in the pin map will be withheld for connecting via object flows instead
    activity_inputs = {k: v for k, v in input_pin_map.items() if isinstance(v, ActivityNode)}
    non_activity_inputs = {k: v for k, v in input_pin_map.items() if k not in activity_inputs}
    pe = make_call_behavior_action(behavior, **non_activity_inputs)
    self.nodes.append(pe)
    # add flows for activities being connected implicitly
    for name, source in activity_inputs.items():
        self.use_value(source, pe.input_pin(name))
    return pe
Activity.call_behavior = activity_call_behavior  # Add to class via monkey patch


def activity_order(self, source: ActivityNode, target: ActivityNode):
    """Add a ControlFlow between the designated source and target nodes in an Activity

    :param source: ActivityNode that is the source of the control flow
    :param target: ActivityNode that is the target of the control flow
    :return: ControlFlow created between source and target
    """
    if source not in self.nodes:
        raise ValueError(f'Source node {source.identity} is not a member of activity {self.identity}')
    if target not in self.nodes:
        raise ValueError(f'Target node {target.identity} is not a member of activity {self.identity}')
    flow = uml.ControlFlow(source=source, target=target)
    self.edges.append(flow)
    return flow
Activity.order = activity_order  # Add to class via monkey patch


def activity_use_value(self, source: ActivityNode, target: ActivityNode):
    """Add an ObjectFlow transferring a value between the designated source and target nodes in an Activity

    Typically, these activities will be either Action Pins or ActivityParameterNodes serving as input or output
    :param source: ActivityNode that is the source of the value
    :param target: ActivityNode that receives the value
    :return: ObjectFlow created between source and target
    """
    if source not in self.nodes:
        raise ValueError(f'Source node {source.identity} is not a member of activity {self.identity}')
    if target not in self.nodes:
        raise ValueError(f'Target node {target.identity} is not a member of activity {self.identity}')
    flow = uml.ObjectFlow(source=source, target=target)
    self.edges.append(flow)
    return flow
Activity.use_value = activity_use_value  # Add to class via monkey patch


###########################################
# Extension methods waiting to be converted

# # Get the Value activity associated with the specified input of a subprotocol
# def subprotocol_input_value(self: SubProtocol, pin: Pin):
#     assert pin in self.input, ValueError("SubProtocol '"+self.identity+"' does not have an input Pin '"+pin+"'")
#     return pin.instance_of.lookup().activity
# SubProtocol.input_value = subprotocol_input_value
#
# # Get the Value activity associated with the specified output of a subprotocol
# def subprotocol_output_value(self: SubProtocol, pin: Pin):
#     assert pin in self.output, ValueError("SubProtocol '" + self.identity + "' does not have an output Pin '" + pin + "'")
#     return pin.instance_of.lookup().activity
# SubProtocol.output_value = subprotocol_output_value

# def activity_input_flows(self):
#     return {x for x in self.get_toplevel().flows if
#             (x.sink.lookup() == self) or
#             (isinstance(self, Executable) and x.sink.lookup() in self.input)}
# Activity.input_flows = activity_input_flows
#
# def activity_output_flows(self):
#     return {x for x in self.get_toplevel().flows if
#             (x.source.lookup() == self) or
#             (isinstance(self, Executable) and x.source.lookup() in self.output)}
# Activity.output_flows = activity_output_flows
#
# def activity_direct_input_flows(self):
#     return {x for x in self.get_toplevel().flows if (x.sink.lookup() == self)}
# Activity.direct_input_flows = activity_direct_input_flows
#
# def activity_direct_output_flows(self):
#     return {x for x in self.get_toplevel().flows if (x.source.lookup() == self)}
# Activity.direct_output_flows = activity_direct_output_flows
#
# def protocol_get_input(self, name):
#     return next(x for x in self.input if x.name==name)
# Protocol.get_input = protocol_get_input
#
#
# def protocol_get_output(self, name):
#     return next(x for x in self.output if x.name==name)
# Protocol.get_output = protocol_get_output
