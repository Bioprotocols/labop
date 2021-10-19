from abc import ABC, abstractmethod
from logging import error

from container_api import matching_containers

import paml
import uml


class BehaviorSpecializationException(Exception):
    pass

class ContainerAPIException(Exception):
    pass


class BehaviorSpecialization(ABC):
    """
    This abstract class defines an API for different conversions from PAML
    to other formats, such as Markdown or Autoprotocol.
    """

    def __init__(self) -> None:
        super().__init__()
        self._behavior_func_map = self._init_behavior_func_map()
        self.top_protocol = None
        self.execution = None

    def initialize_protocol(self, execution: paml.ProtocolExecution):
        self.execution = execution

    @abstractmethod
    def _init_behavior_func_map(self) -> dict:
        pass
    
    @abstractmethod
    def on_begin(self):
        pass

    @abstractmethod
    def on_end(self):
        pass

    def process(self, record):
        node = record.node.lookup()
        if not isinstance(node, uml.CallBehaviorAction):
            return # raise BehaviorSpecializationException(f"Cannot handle node type: {type(node)}")
        elif str(node.behavior) not in self._behavior_func_map:
            raise BehaviorSpecializationException(f"Failed to find handler for behavior: {node.behavior}")
        return self._behavior_func_map[str(node.behavior)](record)

    def resolve_container_spec(self, spec, addl_conditions=None):
        try:
            if addl_conditions:
                possible_container_types = matching_containers(spec, addl_conditions=addl_conditions)
            else:
                possible_container_types = matching_containers(spec)
        except:
            raise ContainerAPIException(f"Cannot resolve specification {spec} with container ontology.  Is the container server running and accessible?")
        return possible_container_types

class DefaultBehaviorSpecialization(BehaviorSpecialization):
    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer" : self.handle,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision" : self.handle,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates" : self.handle,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance" : self.handle,
        }

    def handle(self, record):
        pass

    def on_begin(self):
        pass

    def on_end(self):
        pass