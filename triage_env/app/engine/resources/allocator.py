# triage_env/app/engine/resources/allocator.py
from typing import Optional
from app.core.constants.resources import ESI_COMPATIBILITY_MATRIX, DOCTOR_IDS
from app.core.constants.protocols import ESI_PROCESSING_TIMES
from app.core.models.environment import EnvState

def validate_location(patient_esi: int, resource_id: str, env_state: EnvState) -> tuple[bool, Optional[str]]:
    """Checks if the target resource is medically compatible and currently available."""
    config = ESI_COMPATIBILITY_MATRIX.get(patient_esi, {})
    valid_locations = config.get("valid_locations", [])
    
    if resource_id not in valid_locations:
        return False, f"Resource {resource_id} is not compatible with ESI Level {patient_esi}"
    
    if env_state.resource_occupancy.get(resource_id) is not None:
        return False, f"Resource {resource_id} is already occupied"
        
    return True, None

def validate_doctor_requirement(patient_esi: int, env_state: EnvState) -> tuple[bool, Optional[str]]:
    """Checks if the patient requires a doctor and if one is currently free."""
    requires_doctor = ESI_COMPATIBILITY_MATRIX.get(patient_esi, {}).get("requires_doctor", False)
    if not requires_doctor:
        return True, None

    # A doctor is free if their ID is not present as a value in occupancy mapping
    occupied_patients = env_state.resource_occupancy.values()
    free_doctors = [d for d in DOCTOR_IDS if env_state.resource_occupancy.get(d) is None]
    
    if not free_doctors:
        return False, f"No doctors available for ESI Level {patient_esi} requirement"
    
    return True, None

def execute_assignment(patient_id: str, resource_id: str, patient_esi: int, env_state: EnvState) -> tuple[bool, Optional[str]]:
    """Validates and executes a patient-to-resource assignment including doctor locking."""
    # Run medical and availability validations
    loc_ok, loc_err = validate_location(patient_esi, resource_id, env_state)
    if not loc_ok: return False, loc_err
    
    doc_ok, doc_err = validate_doctor_requirement(patient_esi, env_state)
    if not doc_ok: return False, doc_err

    # Execution phase: Commit the assignment to state
    env_state.resource_occupancy[resource_id] = patient_id
    env_state.resource_release_countdowns[resource_id] = ESI_PROCESSING_TIMES.get(patient_esi, 2)

    # Lock a doctor if required by clinical protocol
    if ESI_COMPATIBILITY_MATRIX[patient_esi]["requires_doctor"]:
        free_doctor = [d for d in DOCTOR_IDS if env_state.resource_occupancy.get(d) is None][0]
        env_state.resource_occupancy[free_doctor] = patient_id
        env_state.resource_release_countdowns[free_doctor] = ESI_PROCESSING_TIMES.get(patient_esi, 2)

    return True, None

def get_occupied_resources(env_state: EnvState) -> dict[str, str]:
    """Returns a view of all currently occupied resource IDs and their patients."""
    return {rid: pid for rid, pid in env_state.resource_occupancy.items() if pid is not None}
