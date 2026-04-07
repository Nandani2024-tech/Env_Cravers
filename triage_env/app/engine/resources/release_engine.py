# triage_env/app/engine/resources/release_engine.py
from typing import Optional
from app.core.constants.resources import DOCTOR_IDS
from app.core.models.environment import EnvState

def _free_resource(resource_id: str, env_state: EnvState) -> Optional[str]:
    """Internal helper to clear a specific resource and return the patient ID that was freed."""
    patient_id = env_state.resource_occupancy.get(resource_id)
    if patient_id is not None:
        env_state.resource_occupancy[resource_id] = None
        env_state.resource_release_countdowns[resource_id] = None
    return patient_id

def process_step_releases(env_state: EnvState) -> list[str]:
    """Decrements resource timers and automatically releases patients whose treatment time has ended."""
    discharged_patients = []
    resource_ids = list(env_state.resource_release_countdowns.keys())

    for rid in resource_ids:
        countdown = env_state.resource_release_countdowns.get(rid)
        if countdown is None or countdown <= 0:
            continue
            
        env_state.resource_release_countdowns[rid] -= 1
        
        # Check if the timer reached zero during this update
        if env_state.resource_release_countdowns[rid] == 0:
            patient_id = _free_resource(rid, env_state)
            if patient_id:
                # Find and release the physician assigned to this specific patient
                for did in DOCTOR_IDS:
                    if env_state.resource_occupancy.get(did) == patient_id:
                        _free_resource(did, env_state)
                
                if patient_id not in discharged_patients:
                    discharged_patients.append(patient_id)
                    
    return discharged_patients

def execute_early_discharge(patient_id: str, env_state: EnvState) -> tuple[bool, Optional[str]]:
    """Handles the DISCHARGE action by manually freeing all resources held by a patient."""
    assigned_resources = [rid for rid, pid in env_state.resource_occupancy.items() if pid == patient_id]
    
    if not assigned_resources:
        return False, f"Patient {patient_id} is not currently assigned to any resource"
        
    for rid in assigned_resources:
        _free_resource(rid, env_state)
        
    return True, None
