import os
import posixpath
from collections import Counter
from typing import List, Set, Iterable
from sbol_factory import SBOLFactory, UMLFactory
import sbol3

# Load ontology and create uml submodule
SBOLFactory('uml_submodule',
            posixpath.join(os.path.dirname(os.path.realpath(__file__)),
            'uml.ttl'),
            'http://bioprotocols.org/uml#')

# Import submodule symbols into top-level uml module
from uml_submodule import *
from .uml_graphviz import *

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


def literal(value, reference: bool = False) -> LiteralSpecification:
    """Construct a UML LiteralSpecification based on the value of the literal passed

    Parameters
    ----------
    value: the value to embed as a literal
    reference: if true, use a reference for a non-TopLevel SBOL rather than embedding as a child object

    Returns
    -------
    LiteralSpecification of the appropriate type for the value
    """
    if isinstance(value, LiteralSpecification):
        return literal(value.value, reference) # if it's a literal, unwrap and rebuild
    elif value is None:
        return LiteralNull()
    elif isinstance(value, str):
        return LiteralString(value=value)
    elif isinstance(value, int):
        return LiteralInteger(value=value)
    elif isinstance(value, bool):
        return LiteralBoolean(value=value)
    elif isinstance(value, float):
        return LiteralReal(value=value)
    elif isinstance(value, sbol3.TopLevel) or (reference and isinstance(value, sbol3.Identified)):
        return LiteralReference(value=value)
    elif isinstance(value, sbol3.Identified):
        return LiteralIdentified(value=value)
    else:
        raise ValueError(f'Don\'t know how to make literal from {type(value)} "{value}"')


###########################################
# Define extension methods for Behavior

def behavior_add_parameter(self, name: str, param_type: str, direction: str, optional: bool = False,
                           default_value: ValueSpecification = None) -> OrderedPropertyValue:
    """Add a Parameter for this Behavior; usually not called directly

    Note: Current assumption is that cardinality is either [0..1] or 1
    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :param direction: should be in or out
    :param optional: True if the Parameter is optional; default is False
    :param default_value: must be specified if Parameter is optional
    :return: Parameter that has been added
    """
    param = Parameter(name=name, type=param_type, direction=direction, is_ordered=True, is_unique=True)
    ordered_param = OrderedPropertyValue(index=len(self.parameters), property_value=param)
    print(param, ordered_param)
    print(ordered_param.__class__.__mro__)
    self.parameters.append(ordered_param)
    param.upper_value = literal(1)  # all parameters are assumed to have cardinality [0..1] or 1 for now
    if optional:
        param.lower_value = literal(0)
    else:
        param.lower_value = literal(1)
    if default_value:
        param.default_value = default_value
    return ordered_param
Behavior.add_parameter = behavior_add_parameter  # Add to class via monkey patch


def behavior_add_input(self, name: str, param_type: str, optional: bool = False,
                       default_value: ValueSpecification = None) -> OrderedPropertyValue:
    """Add an input Parameter for this Behavior

    Note: Current assumption is that cardinality is either [0..1] or 1

    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :param optional: True if the Parameter is optional; default is False
    :param default_value: default value for this parameter
    :return: Parameter that has been added
    """
    return self.add_parameter(name, param_type, PARAMETER_IN, optional, default_value)
Behavior.add_input = behavior_add_input  # Add to class via monkey patch


def behavior_add_output(self, name, param_type) -> OrderedPropertyValue:
    """Add an output Parameter for this Behavior

    :param name: name of the parameter, which will also be used for pins
    :param param_type: URI specifying the type of object that is expected for this parameter
    :return: Parameter that has been added
    """
    return self.add_parameter(name, param_type, PARAMETER_OUT)
Behavior.add_output = behavior_add_output  # Add to class via monkey patch


def behavior_get_inputs(self) -> Iterable[Parameter]:
    """Return all Parameters of type input for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Iterator over Parameters
    """
    return (p for p in self.parameters if p.property_value.direction == PARAMETER_IN)
Behavior.get_inputs = behavior_get_inputs  # Add to class via monkey patch


def behavior_get_input(self, name) -> Parameter:
    """Return a specific input Parameter for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Parameter, or Value error
    """
    print(p for p in self.get_inputs())
    found = [p for p in self.get_inputs() if p.property_value.name == name]
    if len(found) == 0:
        raise ValueError(f'Behavior {self.identity} has no input parameter named {name}')
    elif len(found) > 1:
        raise ValueError(f'Behavior {self.identity} has multiple input parameters named {name}')
    else:
        return found[0]
Behavior.get_input = behavior_get_input  # Add to class via monkey patch


def behavior_get_required_inputs(self):
    """Return all required Parameters of type input for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Iterator over Parameters
    """
    return (p for p in self.get_inputs() if p.property_value.lower_value.value > 0)
Behavior.get_required_inputs = behavior_get_required_inputs  # Add to class via monkey patch


def behavior_get_outputs(self):
    """Return all Parameters of type output for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Iterator over Parameters
    """
    return (p for p in self.parameters if p.property_value.direction == PARAMETER_OUT)
Behavior.get_outputs = behavior_get_outputs  # Add to class via monkey patch


def behavior_get_output(self, name) -> Parameter:
    """Return a specific input Parameter for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Parameter, or Value error
    """
    found = [p for p in self.get_outputs() if p.name == name]
    if len(found) == 0:
        raise ValueError(f'Behavior {self.identity} has no output parameter named {name}')
    elif len(found) > 1:
        raise ValueError(f'Behavior {self.identity} has multiple output parameters named {name}')
    else:
        return found[0]
Behavior.get_output = behavior_get_output  # Add to class via monkey patch


def behavior_get_required_outputs(self):
    """Return all required Parameters of type output for this Behavior

    Note: assumes that type is all either in or out
    Returns
    -------
    Iterator over Parameters
    """
    return (p for p in self.get_outputs() if p.property_value.lower_value.value > 0)
Behavior.get_required_outputs = behavior_get_required_outputs  # Add to class via monkey patch


###########################################
# Define extension methods for ActivityNode

def activitynode_unpin(self: ActivityNode) -> ActivityNode:
    """Find the root node for an ActivityNode: either itself if a Pin, otherwise the owning Action

    Parameters
    ----------
    self: ActivityNode

    Returns
    -------
    self if not a Pin, otherwise the owning Action
    """
    if isinstance(self,Pin):
        action = self.get_parent()
        if not isinstance(action,Action):
            raise ValueError(f'Parent of {self.identity} should be Action, but found {type(action)} instead')
        return action
    else:
        return self
ActivityNode.unpin = activitynode_unpin  # Add to class via monkey patch

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

def call_behavior_action_pin_parameter(self, pin_name: str):
    """Find the behavior parameter corresponding to the pin

    :param pin_name:
    :return: Parameter with specified name
    """
    try:
        pin = self.input_pin(pin_name)
    except:
        try:
            pin = self.output_pin(pin_name)
        except:
            raise ValueError(f'Could not find pin named {pin_name}')
    behavior = self.behavior.lookup()
    [parameter] = [p for p in behavior.parameters if p.property_value.name == pin_name]
    return parameter
CallBehaviorAction.pin_parameter = call_behavior_action_pin_parameter  # Add to class via monkey patch

def add_call_behavior_action(parent: Activity, behavior: Behavior, **input_pin_literals):
    """Create a call to a Behavior and add it to an Activity

    :param parent: Activity to which the behavior is being added
    :param behavior: Behavior to be called
    :param input_pin_literals: map of literal values to be assigned to specific pins
    :return: newly constructed
    """
    # first, make sure that all of the keyword arguments are in the inputs of the behavior
    unmatched_keys = [key for key in input_pin_literals.keys() if key not in (i.property_value.name for i in behavior.get_inputs())]
    if unmatched_keys:
        raise ValueError(f'Specification for "{behavior.display_id}" does not have inputs: {unmatched_keys}')

    # create action
    action = CallBehaviorAction(behavior=behavior)
    parent.nodes.append(action)

    # Instantiate input pins
    for i in id_sort(behavior.get_inputs()):
        if i.property_value.name in input_pin_literals:
            value = input_pin_literals[i.property_value.name]
            # TODO: type check relationship between value and parameter type specification
            action.inputs.append(ValuePin(name=i.property_value.name, is_ordered=i.property_value.is_ordered,
                                          is_unique=i.property_value.is_unique, value=literal(value)))
        else:  # if not a constant, then just a generic InputPin
            action.inputs.append(InputPin(name=i.property_value.name, is_ordered=i.property_value.is_ordered,
                                          is_unique=i.property_value.is_unique))

    # Instantiate output pins
    for o in id_sort(behavior.get_outputs()):
        action.outputs.append(OutputPin(name=o.property_value.name, is_ordered=o.property_value.is_ordered,
                                        is_unique=o.property_value.is_unique))

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
Activity.final = activity_final  # Add to class via monkey patch


def activity_input_value(self, name: str, param_type: str, optional: bool = False,
                       default_value: ValueSpecification = None) -> ActivityParameterNode:
    """Add an input, then return the ActivityParameterNode that refers to that input

    :param self: Activity
    :param name: Name of the input
    :param param_type: type of value expected for the input
    :param optional: True if the Parameter is optional; default is False
    :param default_value: if the input is optional, a default value must be set
    :return: ActivityParameterNode associated with the input
    """
    parameter = self.add_input(name=name, param_type=param_type, optional=optional, default_value=default_value)
    node = ActivityParameterNode(parameter=parameter)
    self.nodes.append(node)
    return node
Activity.input_value = activity_input_value  # Add to class via monkey patch


def activity_designate_output(self, name: str, param_type: str, source: ActivityNode) -> ActivityParameterNode:
    """Add an output, connect it to an ActivityParameterNode, and get its value from the designated node

    :param self: Activity
    :param name: Name of the output
    :param param_type: type of value expected for the output
    :param source: ActivityNode whose ObjectValue output should be routed to the source
    :return: ActivityParameterNode associated with the output
    """
    parameter = self.add_output(name=name, param_type=param_type)
    node = ActivityParameterNode(parameter=parameter)
    self.nodes.append(node)
    self.use_value(source, node)
    return node
Activity.designate_output = activity_designate_output  # Add to class via monkey patch


def activity_initiating_nodes(self) -> List[ActivityNode]:
    """Find all InitialNode and ActivityParameterNode activities.
    These should be the only activities with no in-flow, which can thus initiate execution.

    Parameters
    ----------
    self: Activity

    Returns
    -------
    List of ActivityNodes able to initiate execution
    """
    return [n for n in self.nodes if isinstance(n, InitialNode) or
            (isinstance(n, ActivityParameterNode) and n.parameter and n.parameter.lookup().property_value.direction == PARAMETER_IN)]
Activity.initiating_nodes = activity_initiating_nodes  # Add to class via monkey patch


def activity_incoming_edges(self, node: ActivityNode) -> Set[ActivityEdge]:
    """Find the edges that have the designated node as a target

    Parameters
    ----------
    node: target for edges

    Returns
    -------
    Set of ActivityEdges with node as a target
    """
    return {e for e in self.edges if e.target == node.identity}  # TODO: change to pointer lookup after pySBOL #237
Activity.incoming_edges = activity_incoming_edges  # Add to class via monkey patch


def activity_outgoing_edges(self, node: ActivityNode) -> Set[ActivityEdge]:
    """Find the edges that have the designated node as a source

    Parameters
    ----------
    node: target for edges

    Returns
    -------
    Set of ActivityEdges with node as a source
    """
    return {e for e in self.edges if e.source == node.identity}  # TODO: change to pointer lookup after pySBOL #237
Activity.outgoing_edges = activity_outgoing_edges  # Add to class via monkey patch


def activity_deconflict_objectflow_sources(self, source: ActivityNode) -> ActivityNode:
    '''Avoid nondeterminism in ObjectFlows by injecting ForkNode objects where necessary

    Parameters
    ----------
    self: Activity
    source: node to take a value from, directly or indirectly

    Returns
    -------
    A source to attach to; either the original or an intervening ForkNode
    '''
    # Use original if it's one of the node types that supports multiple dispatch
    if isinstance(source, ForkNode) or isinstance(source, DecisionNode):
        return source
    # Otherwise, find out what targets currently attach:
    current_outflows = [e for e in self.edges if e.source.lookup() is source]
    # Use original if nothing is attached to it
    if len(current_outflows) == 0:
        #print(f'No prior use of {source.identity}, connecting directly')
        return source
    # If the flow goes to a single ForkNode, connect to that ForkNode
    elif len(current_outflows) == 1 and isinstance(current_outflows[0].target.lookup(),ForkNode):
        #print(f'Found an existing fork from {source.identity}, reusing')
        return current_outflows[0].target.lookup()
    # Otherwise, inject a ForkNode and connect all current flows to that instead
    else:
        #print(f'Found no existing fork from {source.identity}, injecting one')
        fork = ForkNode()
        self.nodes.append(fork)
        self.edges.append(ObjectFlow(source=source, target=fork))
        for f in current_outflows:
            f.source = fork # change over the existing flows
        return fork
Activity.deconflict_objectflow_sources = activity_deconflict_objectflow_sources


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


def activity_use_value(self, source: ActivityNode, target: ActivityNode) -> ObjectFlow:
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
    source = self.deconflict_objectflow_sources(source)
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

    # Check that incoming flow counts obey constraints:
    target_counts = Counter([e.target.lookup().unpin() for e in self.edges
                             if isinstance(e.target.lookup(), ActivityNode) ])
    # No InitialNode should have an incoming flow (though an ActivityParameterNode may)
    initial_with_inflow = {n: c for n, c in target_counts.items() if isinstance(n,InitialNode)}
    for n, c in initial_with_inflow.items():
        report.addError(n.identity, None, f'InitialNode must have no incoming edges, but has {c}')
    # No node besides initiating nodes (InitialNode or ActivityParameterNode) should have no incoming flows
    missing_inflow = set(self.nodes) - {n for n, c in target_counts.items()} - set(self.initiating_nodes())
    for n in missing_inflow:
        report.addWarning(n.identity, None, f'Node has no incoming edges, so cannot be executed')

    return report
Activity.validate = activity_validate

# TODO: add a check for loops that can obtain too many or too few values
