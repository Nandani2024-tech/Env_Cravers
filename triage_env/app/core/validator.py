# triage_env/app/core/validator.py
from typing import Optional
from app.core.constants.resources import ALL_RESOURCE_IDS
from app.core.models.action import TriageAction, ActionType
from app.core.models.environment import EnvState
from app.core.models.observation import PatientObservation

class ActionValidator:
    """Gatekeeper for verifying whether an action is legal in the current environment state."""

    def validate(self, action: TriageAction, env_state: EnvState, patient_observations: dict[str, PatientObservation]) -> tuple[bool, Optional[str]]:
        """Routes the incoming action to the appropriate validation logic based on ActionType."""
        if action.action_type == ActionType.CLASSIFY:
            return self._validate_classify(action, env_state)
        elif action.action_type == ActionType.REORDER:
            return self._validate_reorder(action, env_state)
        elif action.action_type == ActionType.ASSIGN:
            return self._validate_assign(action, env_state)
        elif action.action_type == ActionType.REQUEST_INFO:
            return self._validate_request_info(action, env_state)
        elif action.action_type == ActionType.DISCHARGE:
            return self._validate_discharge(action, env_state)
        return False, f"Unknown action type: {action.action_type}"

    def _validate_classify(self, action: TriageAction, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Validates CLASSIFY actions (Tasks 1 and 2 only)."""
        if action.task_id not in ["task_1", "task_2"]:
            return False, f"Action CLASSIFY is not valid in {action.task_id}. Agent must ASSIGN resources."
        
        if action.patient_id not in env_state.patient_hidden_states:
            return False, f"Patient {action.patient_id} not found."
            
        if action.patient_id not in env_state.optimal_queue_order:
            return False, f"Patient {action.patient_id} is already assigned to a resource."
            
        from app.environment import environment
        scenario = environment.current_scenario
        if hasattr(scenario, "classified_patients"):
            if action.patient_id in scenario.classified_patients:
                return False, "Patient already classified"
                
        return True, None

    def _validate_reorder(self, action: TriageAction, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Validates REORDER actions (Tasks 2 and 3 only)."""
        if action.task_id not in ["task_2", "task_3"]:
            return False, f"Action REORDER is not valid in {action.task_id}."
            
        if action.patient_id not in env_state.patient_hidden_states:
            return False, f"Patient {action.patient_id} not found."
            
        if action.patient_id not in env_state.optimal_queue_order:
            return False, f"Patient {action.patient_id} is not in the waiting queue (already assigned)."
            
        # Pydantic conversion gives us an int or a string
        try:
            new_pos = int(action.value)
            queue_len = len(env_state.optimal_queue_order)
            if new_pos < 1 or new_pos > queue_len:
                return False, f"Position {new_pos} for REORDER exceeds queue length of {queue_len}."
        except (ValueError, TypeError):
             return False, f"REORDER position must be an integer, got: {action.value}"
            
        return True, None

    def _validate_assign(self, action: TriageAction, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Validates ASSIGN actions (Task 3 only)."""
        if action.task_id != "task_3":
            return False, f"Action ASSIGN is not valid in {action.task_id}."
            
        if action.patient_id not in env_state.patient_hidden_states:
            return False, f"Patient {action.patient_id} not found."
            
        if action.value not in ALL_RESOURCE_IDS:
             return False, f"Resource {action.value} for ASSIGN is not valid."
             
        if env_state.resource_occupancy.get(action.value) is not None:
             occupied_by = env_state.resource_occupancy[action.value]
             return False, f"Resource {action.value} is already occupied by {occupied_by}."
            
        return True, None

    def _validate_request_info(self, action: TriageAction, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Validates REQUEST_INFO actions (All Tasks)."""
        if action.patient_id not in env_state.patient_hidden_states:
            return False, f"Patient {action.patient_id} not found."
            
        if env_state.patient_hidden_states[action.patient_id].history_unlocked:
            return False, f"History for patient {action.patient_id} already retrieved. Use of REQUEST_INFO on same patient costs a step."
            
        return True, None

    def _validate_discharge(self, action: TriageAction, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Validates DISCHARGE actions (Tasks 2 and 3 only)."""
        if action.task_id not in ["task_2", "task_3"]:
            return False, f"Action DISCHARGE is not valid in {action.task_id}."
            
        if action.patient_id not in env_state.patient_hidden_states:
            return False, f"Patient {action.patient_id} not found."
            
        assigned_resources = [r for r, p in env_state.resource_occupancy.items() if p == action.patient_id]
        if not assigned_resources:
            return False, f"Patient {action.patient_id} is not currently assigned to any resource."
            
        return True, None
