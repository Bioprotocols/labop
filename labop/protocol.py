"""
The Protocol class defines the functions corresponding to the dynamically generated labop class Protocol
"""

import logging
from typing import List, Tuple

import sbol3

import labop.inner as inner
from uml import (
    Activity,
    ActivityEdge,
    ActivityNode,
    Behavior,
    ControlFlow,
    ControlNode,
    DecisionNode,
    ObjectFlow,
    ObjectNode,
    ValueSpecification,
)

from .library import import_library
from .primitive import Primitive
from .utils.helpers import prepare_document

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


class Protocol(inner.Protocol, Activity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_protocol(display_id="demo_protocol", name="DemonstrationProtocol"):
        logger.info("Creating protocol")
        protocol: Protocol = Protocol(display_id)
        protocol.name = name
        protocol.description = protocol.name
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
            primary_incoming_source_node (uml:ActivityNode): primary incoming edge type (control or object) determines output edge types
            decision_input_source_node (uml:ActivityNode, optional): Used to evaluate guards. Defaults to None.
            outgoing_targets (List[Tuple[ValueSpecification, ActivityNode]], optional): List of pairs of guards and nodes for outgoing edges. Defaults to None.
        """

        assert primary_incoming_node
        primary_incoming_flow = (
            ControlFlow(source=primary_incoming_node)
            if isinstance(primary_incoming_node, ControlNode)
            else ObjectFlow(source=primary_incoming_node)
        )
        self.edges.append(primary_incoming_flow)

        decision_input = None

        if decision_input_behavior:
            input_pin_map = {}
            decision_input_control = None
            if decision_input_source:
                input_pin_map["decision_input"] = decision_input_source
            if primary_incoming_node:
                if isinstance(primary_incoming_node, ObjectNode):
                    input_pin_map["primary_input"] = primary_incoming_node
                else:
                    # Make a ControlFlow so that decision_input executes first
                    decision_input_control = ControlFlow(source=primary_incoming_node)

            decision_input = self.execute_primitive(
                decision_input_behavior, **input_pin_map
            )
            if decision_input_control:
                decision_input_control.target = decision_input
                self.edges.append(decision_input_control)

        decision_input_flow = None
        if decision_input_source:
            decision_input_flow = ObjectFlow(source=decision_input_source)
            self.edges.append(decision_input_flow)

        decision = DecisionNode(
            decision_input=decision_input_behavior,
            decision_input_flow=decision_input_flow,
        )
        self.nodes.append(decision)

        if decision_input:
            # Flow that communicates the return value of the decision_input behavior execution to the decision
            decision_input_to_decision_flow = ObjectFlow(
                source=decision_input.output_pin("return"), target=decision
            )
            self.edges.append(decision_input_to_decision_flow)

        primary_incoming_flow.target = decision
        if decision_input_flow:
            decision_input_flow.target = decision

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
