# triage_env/app/graders/task_3/time_scorer.py
from app.core.constants.thresholds import MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION
from app.core.models.environment import PatientHiddenState
from app.core.models.observation import PatientObservation

def score_wait_times(patient_hidden_states: dict[str, PatientHiddenState], patient_observations: dict[str, PatientObservation]) -> float:
    """Calculates a collective wait-time efficiency score for all patients in the scenario."""
    total_score = 0.0
    count = len(patient_observations)
    
    if count == 0:
        return 1.0

    for pid, obs in patient_observations.items():
        hidden = patient_hidden_states[pid]
        # Benchmark limit: Clinical threshold for this ESI, or a default of 20 steps
        allowed = MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION.get(hidden.true_esi_level) or 20
        
        # Calculate how much of the "safe" window the patient spent waiting (0.0 to 1.0)
        patient_score = max(0.0, 1.0 - (obs.wait_steps / allowed))
        total_score += patient_score
        
    return total_score / count
