"""
The ActivityNodeExecution class defines the functions corresponding to the dynamically generated labop class ActivityNodeExecution
"""

from typing import Callable, List

from uml import (
    ActivityNode,
    CallBehaviorAction,
    ForkNode,
    InputPin,
    Parameter,
    labop_hash,
)

from . import inner


class ActivityNodeExecution(inner.ActivityNodeExecution):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity) + hash(self.get_node())

    def get_node(self) -> ActivityNode:
        return self.node.lookup()

    def get_incoming_flows(self) -> List["ActivityEdgeFlow"]:
        return [flow.lookup() for flow in self.incoming_flows]

    def check_next_tokens(
        self,
        tokens: List["ActivityEdgeFlow"],
        node_outputs: Callable,
        perimssive: bool,
        sample_format: str,
    ):
        pass

    def parameter_value_map(self):
        values = [
            v for t in self.get_incoming_flows() if t.value is not None for v in t.value
        ]
        values = None if len(values) == 0 else values
        values = values[0] if values and len(values) == 1 else values

        if values is None:
            return {}
        else:
            return {self.get_node().name: values}

    def get_token_source(
        self,
        parameter: Parameter,
        target=None,
    ) -> "CallBehaviorExecution":
        # Get a ActivityNodeExecution that produced this token assigned to this ActivityNodeExecution parameter.
        # The immediate predecessor will be the token_source

        node = self.get_node()
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
    ) -> "CallBehaviorExecution":
        """Look for the InitialNode for the Activity including self and identify a Calling CallBehaviorExecution (if present)

        Args:
            self (ActivityNodeExecution): current search node

        Returns:
            CallBehaviorExecution: CallBehaviorExecution
        """
        from .call_behavior_execution import CallBehaviorExecution

        node = self.node.lookup()
        protocol = node.protocol()
        initial = protocol.initial()
        initial_execution = next(
            e for e in reversed(engine.ex.executions) if e.node == initial.identity
        )
        incoming_initial_flows = initial_execution.incoming_flows
        try:
            caller = next(
                n.lookup().token_source.lookup()
                for n in reversed(incoming_initial_flows)
                if isinstance(
                    n.lookup().token_source.lookup(),
                    CallBehaviorExecution,
                )
            )
        except StopIteration:
            return None
        return caller
