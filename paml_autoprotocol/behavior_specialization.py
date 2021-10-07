from abc import ABC, abstractmethod
from logging import error

class BehaviorSpecializationException(Exception):
    pass

class BehaviorSpecialization(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._behavior_func_map = self._init_behavior_func_map()

    @abstractmethod
    def _init_behavior_func_map(self) -> dict:
        pass
    
    @abstractmethod
    def on_begin(self):
        pass

    @abstractmethod
    def on_end(self):
        pass

    def process(self, node, inputs, outputs):
        if str(node.behavior) not in self._behavior_func_map:
            raise BehaviorSpecializationException(f"Failed to find handler for behavior: {node.behavior}")
        return self._behavior_func_map[str(node.behavior)](node, inputs, outputs)
