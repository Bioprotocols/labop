import logging

from uml import ActivityEdgeFlow, CallBehaviorAction, Pin

from .activity_node_execution import ActivityNodeExecution

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


class ExecutionIssue(object):
    pass


class ExecutionWarning(ExecutionIssue):
    pass


class ExecutionError(ExecutionIssue):
    pass


class ProtocolExecutionExtractor:
    def extract_record(self, record: ActivityNodeExecution):
        pass

    def extract_token(self, token: ActivityEdgeFlow):
        pass


class JSONProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def __init__(self) -> None:
        super().__init__()
        self.extraction_map = {CallBehaviorAction: self.extract_call_behavior_action}

    def extract_call_behavior_action(self, token: ActivityEdgeFlow):
        return super().extract_token(token)

    def extract_record(self, record: ActivityNodeExecution):
        behavior_str = (
            record.node.lookup().behavior
            if isinstance(record.node.lookup(), CallBehaviorAction)
            else (
                (
                    record.node.lookup().get_parent().behavior,
                    record.node.lookup().name,
                )
                if isinstance(record.node.lookup(), Pin)
                else ""
            )
        )
        record_str = f"{record.node} ({behavior_str})"
        return record_str


class StringProtocolExecutionExtractor(ProtocolExecutionExtractor):
    def extract_record(self, record: ActivityNodeExecution):
        behavior_str = (
            record.node.lookup().behavior
            if isinstance(record.node.lookup(), CallBehaviorAction)
            else (
                (
                    record.node.lookup().get_parent().behavior,
                    record.node.lookup().name,
                )
                if isinstance(record.node.lookup(), Pin)
                else ""
            )
        )
        record_str = f"{record.node} ({behavior_str})"
        return record_str
