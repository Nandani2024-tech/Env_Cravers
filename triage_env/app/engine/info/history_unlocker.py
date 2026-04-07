# triage_env/app/engine/info/history_unlocker.py
from typing import Optional
from app.core.models.environment import EnvState
from app.core.models.observation import MedicalHistory, PatientObservation

def execute_request_info(patient_id: str, env_state: EnvState) -> tuple[bool, Optional[str], Optional[MedicalHistory]]:
    """Handles the REQUEST_INFO action by revealing hidden medical history for a patient."""
    if patient_id not in env_state.patient_hidden_states:
        return False, f"Patient {patient_id} not found", None
        
    hidden_state = env_state.patient_hidden_states[patient_id]
    
    if hidden_state.history_unlocked:
        return False, f"History for patient {patient_id} already retrieved. Use of REQUEST_INFO on same patient costs a step.", None
        
    hidden_state.history_unlocked = True
    return True, None, hidden_state.medical_history

def apply_history_to_observation(patient_id: str, history: MedicalHistory, patient_observations: dict[str, PatientObservation]) -> dict[str, PatientObservation]:
    """Applies the unlocked medical history to the patient's observation payload."""
    if patient_id in patient_observations:
        obs = patient_observations[patient_id]
        patient_observations[patient_id] = obs.model_copy(update={"hidden_history": history})
        
    return patient_observations
