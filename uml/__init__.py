import os
import posixpath
from collections import Counter
from sbol_factory import SBOLFactory, UMLFactory
import sbol3

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)), 'uml.ttl'),
                          'http://bioprotocols.org/uml#')
__umlfactory__ = UMLFactory(__factory__)


# Workaround for pySBOL3 issue #231: should be applied to every iteration on a collection of SBOL objects
# TODO: delete after resolution of pySBOL3 issue #231
def id_sort(i: iter):
    sortable = list(i)
    sortable.sort(key=lambda x: x.identity if isinstance(x, sbol3.Identified) else x)
    return sortable


###########################################
# Define extension methods for ValueSpecification

# TODO: move constants into ontology after resolution of https://github.com/SynBioDex/sbol_factory/issues/14
PARAMETER_IN = 'http://bioprotocols.org/uml#in'
PARAMETER_OUT = 'http://bioprotocols.org/uml#out'


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

def behavior_add_parameter(self, name: str, param_type: str, direction: str, optional: bool = False):
    """Add a Parameter for this Behavior; usually not called directly

    Note: Current assumption is that cardinality is either [0..1] or 1
    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :param direction: should be 'in' or 'out'
    :param optional: True if the Parameter is optional; default is False
    :return: Parameter that has been added
    """
    param = Parameter(name=name, type=param_type, direction=direction, is_ordered=True, is_unique=True)
    self.parameters.append(param)
    param.upper_value = literal(1)  # all parameters are assumed to have cardinality [0..1] or 1 for now
    if optional:
        param.lower_value = literal(0)
    else:
        param.lower_value = literal(1)
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
    return self.add_parameter(name, param_type, PARAMETER_IN, optional)
Behavior.add_input = behavior_add_input  # Add to class via monkey patch


def behavior_add_output(self, name, param_type):
    """Add an output Parameter for this Behavior

    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :return: Parameter that has been added
    """
    return self.add_parameter(name, param_type, PARAMETER_OUT)
Behavior.add_output = behavior_add_output  # Add to class via monkey patch


def behavior_get_inputs(self):
    """Return all Parameters of type input for this Behavior

    Note: assumes that type is all either in or out
    :return: Iterator over Parameters
    """
    return (p for p in self.parameters if p.direction == PARAMETER_IN)
Behavior.get_inputs = behavior_get_inputs  # Add to class via monkey patch


def behavior_get_outputs(self):
    """Return all Parameters of type output for this Behavior

    Note: assumes that type is all either in or out
    :return: Iterator over Parameters
    """
    return (p for p in self.parameters if p.direction == PARAMETER_OUT)
Behavior.get_outputs = behavior_get_outputs  # Add to class via monkey patch


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


def add_call_behavior_action(parent: Activity, behavior: Behavior, **input_pin_literals):
    """Create a call to a Behavior and add it to an Activity

    :param parent: Activity to which the behavior is being added
    :param behavior: Behavior to be called
    :param input_pin_literals: map of literal values to be assigned to specific pins
    :return: newly constructed
    """
    # first, make sure that all of the keyword arguments are in the inputs of the behavior
    unmatched_keys = [key for key in input_pin_literals.keys() if key not in (i.name for i in behavior.get_inputs())]
    if unmatched_keys:
        raise ValueError(f'Specification for "{behavior.display_id}" does not have inputs: {unmatched_keys}')

    # create action
    action = CallBehaviorAction(behavior=behavior)
    parent.nodes.append(action)

    # Instantiate input pins
    for i in id_sort(behavior.get_inputs()):
        if i.name in input_pin_literals:
            value = input_pin_literals[i.name]
            # TODO: type check relationship between value and parameter type specification
            action.inputs.append(ValuePin(name=i.name, is_ordered=i.is_ordered, is_unique=i.is_unique,
                                          value=literal(value)))
        else:  # if not a constant, then just a generic InputPin
            action.inputs.append(InputPin(name=i.name, is_ordered=i.is_ordered, is_unique=i.is_unique))

    # Instantiate output pins
    for o in id_sort(behavior.get_outputs()):
        action.outputs.append(OutputPin(name=o.name, is_ordered=o.is_ordered, is_unique=o.is_unique))

    return action


###########################################
# Define extension methods for Activity

def activity_initial(self):
    """Find or create an initial node in an Activity.

    Note that while UML allows multiple initial nodes, use of this routine assumes a single one is sufficient.
    :return: InitialNode for Activity
    """

    initial = [a for a in self.nodes if isinstance(a, InitialNode)]
    if not initial:
        self.nodes.append(InitialNode())
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
    final = [a for a in self.nodes if isinstance(a, FinalNode)]
    if not final:
        self.nodes.append(FlowFinalNode())
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
    cba = add_call_behavior_action(self, behavior, **non_activity_inputs)
    # add flows for activities being connected implicitly
    for name, source in id_sort(activity_inputs.items()):
        self.use_value(source, cba.input_pin(name))
    return cba
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
    flow = ControlFlow(source=source, target=target)
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
    if source.get_toplevel() is not self:  # check via toplevel, because pins are not directly in the node list
        raise ValueError(f'Source node {source.identity} is not a member of activity {self.identity}')
    if target.get_toplevel() is not self:
        raise ValueError(f'Target node {target.identity} is not a member of activity {self.identity}')
    flow = ObjectFlow(source=source, target=target)
    self.edges.append(flow)
    return flow
Activity.use_value = activity_use_value  # Add to class via monkey patch


def activity_validate(self, report: sbol3.ValidationReport = None) -> sbol3.ValidationReport:
    '''Checks to see if the activity has any undesirable non-deterministic edges
    Parameters
    ----------
    self
    report

    Returns
    -------

    '''
    report = super(Activity, self).validate(report)
    # Check for objects with multiple outgoing ObjectFlow edges that are not of type ForkNode or DecisionNode
    source_counts = Counter([e.source.lookup() for e in self.edges if isinstance(e,ObjectFlow)])
    multi_targets = {n: c for n, c in source_counts.items() if c>1 and not (isinstance(n,ForkNode) or isinstance(n,DecisionNode))}
    for n, c in multi_targets.items():
        report.addWarning(n.identity, None, f'ActivityNode has {c} outgoing edges: multi-edges can cause nondeterministic flow')
    return report
Activity.validate = activity_validate

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
