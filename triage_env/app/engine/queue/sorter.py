# triage_env/app/engine/queue/sorter.py
from typing import Optional
from app.core.models.environment import EnvState, PatientHiddenState
from app.core.models.observation import PatientObservation

def calculate_optimal_queue(
    patient_hidden_states: dict[str, PatientHiddenState],
    patient_observations: dict[str, PatientObservation],
    current_queue: list[str]
) -> list[str]:
    """Computes the medically correct queue ordering based on ESI levels and wait time."""
    return sorted(
        current_queue,
        key=lambda pid: (
            patient_hidden_states[pid].true_esi_level,      # Primary: ESI ascending
            -patient_observations[pid].wait_steps            # Secondary: wait time descending
        )
    )

def execute_reorder(patient_id: str, new_position: int, env_state: EnvState) -> tuple[bool, Optional[str]]:
    """Handles the REORDER action by manually moving a patient in the optimal queue order."""
    assigned_patients = [pid for pid in env_state.resource_occupancy.values() if pid is not None]
    if patient_id in assigned_patients:
        return False, f"Patient {patient_id} is already assigned to a resource and cannot be reordered"

    if patient_id not in env_state.optimal_queue_order:
        return False, f"Patient {patient_id} not found in current queue"

    queue_len = len(env_state.optimal_queue_order)
    if new_position > queue_len or new_position < 1:
        return False, f"Position {new_position} exceeds queue length of {queue_len}"

    env_state.optimal_queue_order.remove(patient_id)
    env_state.optimal_queue_order.insert(new_position - 1, patient_id)
    return True, None

def increment_wait_steps(env_state: EnvState, patient_observations: dict[str, PatientObservation]) -> dict[str, PatientObservation]:
    """Increments the wait_steps counter for all patients currently in the waiting queue."""
    for pid in env_state.optimal_queue_order:
        if pid in patient_observations:
            obs = patient_observations[pid]
            patient_observations[pid] = obs.model_copy(update={"wait_steps": obs.wait_steps + 1})
    return patient_observations

def get_queue_score(agent_queue: list[str], optimal_queue: list[str]) -> float:
    """Calculates a normalized score comparing the agent's queue ordering against the optimal queue.
    Normalization formula: 1.0 - (sum of abs pos differences) / (max possible difference from reverse array).
    """
    if not optimal_queue or not agent_queue:
        return 1.0

    total_diff = 0
    for i, pid in enumerate(agent_queue):
        if pid in optimal_queue:
            optimal_idx = optimal_queue.index(pid)
            total_diff += abs(i - optimal_idx)

    n = len(optimal_queue)
    max_possible_difference = sum(abs(i - (n - 1 - i)) for i in range(n))

    if max_possible_difference == 0:
        return 1.0

    return max(0.0, 1.0 - (total_diff / max_possible_difference))
