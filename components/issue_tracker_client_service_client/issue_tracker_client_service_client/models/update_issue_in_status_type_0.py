from enum import Enum


class UpdateIssueInStatusType0(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    TO_DO = "to_do"

    def __str__(self) -> str:
        return str(self.value)
