import sys
import os
from abc import ABC, abstractmethod
from logging import error
import logging

import labop
from labop.primitive_execution import input_parameter_map
import uml
import json

l = logging.getLogger(__file__)
l.setLevel(logging.WARN)


class BehaviorSpecializationException(Exception):
    pass


class ContainerAPIException(Exception):
    pass


class BehaviorSpecialization(ABC):
    """
    This abstract class defines an API for different conversions from LabOP
    to other formats, such as Markdown or Autoprotocol.
    """

    def __init__(self) -> None:
        super().__init__()
        self._behavior_func_map = self._init_behavior_func_map()
        self.top_protocol = None
        self.execution = None
        self.issues = []
        self.out_dir = None
        self.objects = {}

        # This data field holds the results of the specialization
        self.data = []

    def initialize_protocol(self, execution: labop.ProtocolExecution, out_dir=None):
        self.execution = execution
        self.out_dir = out_dir

    def _init_behavior_func_map(self) -> dict:
        return {}

    def on_begin(self, execution: labop.ProtocolExecution):
        self.data = []

    def on_end(self, execution: labop.ProtocolExecution):
        try:
            dot_graph = execution.to_dot()
            self.data.append(str(dot_graph.source))
        except Exception as e:
            msg = "Could not render dot graph for execution in DefaultBehaviorSpecialization"
            l.warn(msg)
            self.issues.append(msg)

        self.data = json.dumps(self.data)
        if self.out_dir:
            with open(os.path.join(self.out_dir, f"{self.__class__.__name__}.json"), "w") as f:
                f.write(self.data)

    def process(self, record, execution: labop.ProtocolExecution):
        try:
            node = record.node.lookup()
            if not isinstance(node, uml.CallBehaviorAction):
                return  # raise BehaviorSpecializationException(f"Cannot handle node type: {type(node)}")

            # Subprotocol specializations
            behavior = node.behavior.lookup()
            if isinstance(behavior, labop.Protocol):
                return self._behavior_func_map[behavior.type_uri](
                    record, execution
                )

            # Individual Primitive specializations
            elif str(node.behavior) not in self._behavior_func_map:
                l.warning(
                    f"Failed to find handler for behavior: {node.behavior}"
                )
                return self.handle(record, execution)
            return self._behavior_func_map[str(node.behavior)](
                record, execution
            )
        except Exception as e:
            l.warn(
                f"{self.__class__} Could not process() ActivityNodeException: {record}: {e}"
            )
            self.handle_process_failure(record, e)

    def handle_process_failure(self, record, e):
        self.issues.append(e)
        raise e

    def handle(self, record, execution):
        # Save basic information about the execution record
        node = record.node.lookup()
        params = input_parameter_map(
            [
                pv
                for pv in record.call.lookup().parameter_values
                if pv.parameter.lookup().property_value.direction
                == uml.PARAMETER_IN
            ]
        )
        params = {p: str(v) for p, v in params.items()}
        node_data = {
            "identity": node.identity,
            "behavior": node.behavior,
            "parameters": params,
        }
        self.update_objects(record)
        self.data.append(node_data)

    def update_objects(self, record: labop.ActivityNodeExecution):
        """
        Update the objects processed by the record.

        Parameters
        ----------
        record : labop.ActivityNodeExecution
            A step that modifies objects.
        """
        pass

    def resolve_container_spec(self, spec, addl_conditions=None):
        try:
            from container_api import matching_containers

            if "container_api" not in sys.modules:
                raise Exception(
                    "Could not import container_api, is it installed?"
                )

            if addl_conditions:
                possible_container_types = matching_containers(
                    spec, addl_conditions=addl_conditions
                )
            else:
                possible_container_types = matching_containers(spec)
        except:
            raise ContainerAPIException(
                f"Cannot resolve specification {spec} with container ontology.  Is the container server running and accessible?"
            )
        return possible_container_types

class DefaultBehaviorSpecialization(BehaviorSpecialization):
    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": self.handle,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": self.handle,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PlateCoordinates": self.handle,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.handle,
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": self.handle,
            "http://bioprotocols.org/labop#Protocol": self.handle,
        }
