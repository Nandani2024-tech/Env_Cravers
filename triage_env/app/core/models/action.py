# triage_env/app/core/models/action.py
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, model_validator
from app.core.constants.resources import ALL_RESOURCE_IDS

class ActionType(str, Enum):
    """Enumeration of valid agent action categories in the triage environment."""
    CLASSIFY = "classify"
    REORDER = "reorder"
    ASSIGN = "assign"
    REQUEST_INFO = "request_info"
    DISCHARGE = "discharge"

class TriageAction(BaseModel):
    """Pydantic model representing a single agent decision/action."""
    # The identifier for the current task context (e.g., 'task_1')
    task_id: str
    # The category of the action to be performed
    action_type: ActionType
    # The unique identifier of the target patient
    patient_id: str
    # The decision payload (ESI level, queue index, or resource ID)
    value: Optional[Union[int, str]] = None

    @model_validator(mode='after')
    def validate_action_value(self) -> "TriageAction":
        """Ensures the value field contains valid data for the specific action type."""
        if self.action_type == ActionType.CLASSIFY:
            try:
                val = int(self.value)
                if not (1 <= val <= 5):
                    raise ValueError(f"CLASSIFY action requires value between 1 and 5, got: {val}")
            except (ValueError, TypeError):
                raise ValueError(f"CLASSIFY action requires an integer value between 1 and 5, got: {self.value}")

        elif self.action_type == ActionType.REORDER:
            try:
                val = int(self.value)
                if val < 1:
                    raise ValueError(f"REORDER action requires a positive integer starting from 1, got: {val}")
            except (ValueError, TypeError):
                raise ValueError(f"REORDER action requires an integer value for queue position, got: {self.value}")

        elif self.action_type == ActionType.ASSIGN:
            if not isinstance(self.value, str) or self.value not in ALL_RESOURCE_IDS:
                raise ValueError(f"ASSIGN action requires a valid resource ID from ALL_RESOURCE_IDS, got: {self.value}")

        return self
