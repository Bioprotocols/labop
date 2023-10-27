"""
The Protocol class defines the functions corresponding to the dynamically generated labop class Protocol
"""

import logging
from collections import Counter
from typing import List, Tuple

import sbol3

from uml import (
    Activity,
    ActivityNode,
    Behavior,
    ControlFlow,
    ControlNode,
    DecisionNode,
    FinalNode,
    InitialNode,
    ObjectFlow,
    ObjectNode,
    ValueSpecification,
)
from uml.call_behavior_action import CallBehaviorAction
from uml.utils import WellFormednessError, WellFormednessIssue

from . import inner
from .library import import_library
from .primitive import Primitive
from .utils.helpers import prepare_document

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


class Protocol(inner.Protocol, Activity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial = self.initial()
        self._final = self.final()
        self.order(self._initial, self._final)
        self._where_defined = self.get_where_defined()

    def create_protocol(display_id="demo_protocol", name="DemonstrationProtocol"):
        logger.info("Creating protocol")
        protocol: Protocol = Protocol(display_id)
        protocol.name = name
        protocol.description = protocol.name

        # Ensure that protocol has an InitialNode and a FinalNode in the correct order
        protocol.order(protocol.initial(), protocol.final())

        return protocol

    def initialize_protocol(
        display_id="demo_protocool",
        name="DemonstrationProtocol",
        namespace="https://bioprotocols.org/demo/",
    ) -> Tuple["Protocol", sbol3.Document]:
        #############################################
        # set up the document
        doc: sbol3.Document = prepare_document(namespace=namespace)

        #############################################
        # Import the primitive libraries
        import_library("liquid_handling")
        import_library("sample_arrays")
        import_library("spectrophotometry")

        #############################################
        # Create the protocol
        protocol = Protocol.create_protocol(display_id=display_id, name=name)
        doc.add(protocol)
        return protocol, doc

    def get_last_step(self):
        return self.last_step if hasattr(self, "last_step") else self.initial()

    def execute_primitive(self, primitive, **input_pin_map):
        """Create and add an execution of a Primitive to a Protocol

        :param primitive: Primitive to be invoked (object or string name)
        :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
        :return: CallBehaviorAction that invokes the Primitive
        """

        # Convenience converter: if given a string, use it to look up the primitive
        if isinstance(primitive, str):
            primitive = Primitive.get_primitive(self.document, primitive)
        return self.call_behavior(primitive, **input_pin_map)

    def primitive_step(self, primitive: Primitive, **input_pin_map):
        """Use a Primitive as an Action in a Protocol, automatically serialized to follow the last step added

        Note that this will not give a stable order if adding to a Protocol that has been deserialized, since
        information about the order in which steps were created is not stored.
        :param primitive: Primitive to be invoked (object or string name)
        :param input_pin_map: literal value or ActivityNode mapped to names of Behavior parameters
        :return: CallBehaviorAction that invokes the Primitive
        """
        pe = self.execute_primitive(primitive, **input_pin_map)
        self.order(self.get_last_step(), pe)
        self.last_step = pe  # update the last step
        return pe

    def make_decision_input_activity(
        self,
        decision_input_behavior: Behavior,
        decision_input_source: ActivityNode = None,
    ) -> CallBehaviorAction:
        input_pin_map = (
            {"decision_input": decision_input_source}
            if decision_input_source is not None
            else {}
        )

        decision_input = self.execute_primitive(
            decision_input_behavior, **input_pin_map
        )
        return decision_input

    def make_decision_node(
        self,
        primary_incoming_node: ActivityNode,
        decision_input_behavior: Behavior = None,
        decision_input_source: ActivityNode = None,
        outgoing_targets: List[Tuple[ValueSpecification, ActivityNode]] = None,
    ):
        """
        Make a uml:DecisionNode using optionally specified incoming and outgoing nodes.
        Returns a uml:DecisionNode and a set of edges connecting incoming and outgoing nodes.

        Args:
            primary_incoming_node (uml:ActivityNode): primary incoming edge type (control or object) determines output edge types
            decision_input_behavior (uml.Behavior): Behavior computing decision predicate
            decision_input_source (uml:ActivityNode, optional): Used to evaluate guards. Defaults to None.
            outgoing_targets (List[Tuple[ValueSpecification, ActivityNode]], optional): List of pairs of guards and nodes for outgoing edges. Defaults to None.
        """

        assert primary_incoming_node

        decision_input = (
            self.make_decision_input_activity(
                decision_input_behavior,
                decision_input_source=decision_input_source,
            )
            if decision_input_behavior is not None
            else None
        )

        # Link decision input flow
        decision_input_flow = None

        if decision_input:
            # if decision_input_source is not None:
            # # link decision_input_source to decision_input
            # decision_input_flow = ObjectFlow(
            #     source=decision_input_source, target=decision_input.input_pin("decision_input")
            # )
            # self.edges.append(decision_input_flow)

            # Order decision input after primary incoming node
            decision_input_control = ControlFlow(
                source=primary_incoming_node, target=decision_input
            )
            self.edges.append(decision_input_control)
        elif decision_input_source is not None:
            decision_input_flow = ObjectFlow(
                source=decision_input_source, target=decision
            )
            self.edges.append(decision_input_flow)

        decision = DecisionNode(
            decision_input=decision_input_behavior,
            decision_input_flow=decision_input_flow,
        )
        self.nodes.append(decision)

        if decision_input:
            # Link Flow that communicates the return value of the decision_input behavior execution to the decision
            decision_input_to_decision_flow = ObjectFlow(
                source=decision_input.output_pin("return"), target=decision
            )
            self.edges.append(decision_input_to_decision_flow)

        # Control nodes and CallBehaviorAction nodes provide control flow.  ActivityParameterNode and Pins provide object flows
        primary_incoming_flow = (
            ControlFlow(source=primary_incoming_node, target=decision)
            if isinstance(primary_incoming_node, ControlNode)
            or isinstance(primary_incoming_node, CallBehaviorAction)
            else ObjectFlow(source=primary_incoming_node)
        )
        self.edges.append(primary_incoming_flow)

        # Make edges for outgoing_targets
        if outgoing_targets:
            for guard, target in outgoing_targets:
                decision.add_decision_output(self, guard, target)

        return decision

    def template(self):
        """
        Create a template instantiation of a protocol.  Used for populating UI elements.
        :param
        :return: str
        """
        return f'protocol = labop.Protocol(\n\t"Identity",\n\tname="Name",\n\tdescription="Description")'

    def is_well_formed(self) -> List[WellFormednessIssue]:
        """
        A protocol is well formed if:
        - each ActivityNode is well formed
        - each ActivityEdge is well formed
        - has an initial node
        - has a final node
        """
        issues = []

        validation_report = self.validate()

        issues += [
            WellFormednessError(self.document.find(e.object_id), e.message)
            for e in validation_report.errors
        ]
        issues += [
            WellFormednessError(self.document.find(e.object_id), e.message)
            for e in validation_report.warnings
        ]

        for node in self.get_nodes():
            issues += node.is_well_formed()

        for edge in self.get_edges():
            issues += edge.is_well_formed()

        if not any([isinstance(node, InitialNode) for node in self.nodes]):
            issues += [
                WellFormednessError(
                    self,
                    f"Protocol does not include an InitialNode",
                    f"Calling protocol.initial() will add an InitialNode to protocol.",
                )
            ]

        if not any([isinstance(node, FinalNode) for node in self.nodes]):
            issues += [
                WellFormednessError(
                    self,
                    f"Protocol does not include an FinalNode",
                    f"Calling protocol.final() will add an FinalNode to protocol.",
                )
            ]

        return issues

    def remove_duplicates(self):
        """
        Remove duplicate nodes, preferring to remove those without edges
        """
        duplicates = {
            n.identity: set({n1 for n1 in self.nodes if n1.identity == n.identity})
            for n in self.nodes
        }
        for id, dup in duplicates.items():
            if len(dup) > 1:
                # Remove nodes that are not connected by an edge
                targets = Counter(
                    e.get_target() for e in self.edges if e.get_target() in dup
                )
                sources = Counter(
                    e.get_source() for e in self.edges if e.get_source() in dup
                )
                dups_to_remove = [d for d in dup if targets[d] == 0 and sources[d] == 0]
                for n in dups_to_remove:
                    del self.nodes[self.nodes.index(n)]

    def auto_advance(self):
        return True

    def get_behaviors(self) -> List[Behavior]:
        activities = [
            n.get_behavior() for n in self.nodes if isinstance(n, ActivityNode)
        ]
        return activities
