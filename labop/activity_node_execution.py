"""
The ActivityNodeExecution class defines the functions corresponding to the dynamically generated labop class ActivityNodeExecution
"""

from typing import Callable, List

import sbol3

from labop import inner
from labop.activity_edge_flow import ActivityEdgeFlow
from uml import (
    PARAMETER_OUT,
    ActivityEdge,
    ActivityNode,
    ActivityParameterNode,
    CallBehaviorAction,
    ControlFlow,
    ForkNode,
    InitialNode,
    InputPin,
    LiteralSpecification,
    ObjectFlow,
    OutputPin,
    Parameter,
    flow_final_node,
    literal,
)


class ActivityNodeExecution(inner.ActivityNodeExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_node(self) -> ActivityNode:
        return self.node.lookup()

    def get_incoming_flows(self) -> List[ActivityEdgeFlow]:
        return [flow.lookup() for flow in self.incoming_flows]

    def check_next_tokens(
        self,
        tokens: List["ActivityEdgeFlow"],
        node_outputs: Callable,
        sample_format: str,
    ):
        pass

    def parameter_value_map(self):
        # This is an abstract function that shouldn't be called directly.
        return {}

    def get_token_source(
        self,
        parameter: Parameter,
        target=None,
    ) -> "CallBehaviorExecution":
        # Get a ActivityNodeExecution that produced this token assigned to this ActivityNodeExecution parameter.
        # The immediate predecessor will be the token_source

        node = self.node.lookup()
        print(self.identity + " " + node.identity + " param = " + str(parameter))
        if (
            isinstance(node, InputPin)
            or isinstance(node, ForkNode)
            or isinstance(node, CallBehaviorAction)
        ):
            main_target = target if target else self
            for flow in self.incoming_flows:
                source = flow.lookup().get_token_source(parameter, target=main_target)
                if source:
                    return source
            return None
        else:
            return self

    def get_calling_behavior_execution(
        self,
        visited=None,
    ):
        """Look for the InitialNode for the Activity including self and identify a Calling CallBehaviorExecution (if present)

        Args:
            self (ActivityNodeExecution): current search node

        Returns:
            CallBehaviorExecution: CallBehaviorExecution
        """
        node = self.node.lookup()
        if visited is None:
            visited = set({})
        if isinstance(node, InitialNode):
            # Check if there is a CallBehaviorExecution incoming_flow
            try:
                caller = next(
                    n.lookup().token_source.lookup()
                    for n in self.incoming_flows
                    if isinstance(
                        n.lookup().token_source.lookup(),
                        CallBehaviorExecution,
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
                        parent_activity_node.get_calling_behavior_execution(
                            visited=visited
                        )
                    )
                    if calling_behavior_execution:
                        return calling_behavior_execution
            return None
