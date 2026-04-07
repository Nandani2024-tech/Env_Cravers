# triage_env/app/graders/task_2_grader.py
from app.core.models.environment import EnvState, PatientHiddenState
from app.core.models.observation import PatientObservation
from app.core.config import settings
from app.engine.queue.sorter import get_queue_score, calculate_optimal_queue

def grade_task_2(env_state: EnvState, patient_hidden_states: dict, patient_observations: dict, final_queue: list[str]) -> float:
    """Calculates the finale episode score combining accuracy and queue prioritization (Task 2)."""
    # Classification accuracy score (weighted 40%)
    classification_score = env_state.stats.correct_classifications / 10.0
    
    # Priority sorting score (weighted 40%)
    optimal_queue = calculate_optimal_queue(patient_hidden_states, patient_observations, final_queue)
    queue_score = get_queue_score(final_queue, optimal_queue)
    
    # Efficiency bonus based on steps taken vs maximum (weighted 20%)
    speed_score = max(0.0, 1.0 - (env_state.stats.total_steps / settings.MAX_STEPS))
    
    # Combined penalties for illegal actions and preventable deteriorations
    penalty = (env_state.stats.invalid_actions * 0.05) + (env_state.stats.preventable_deteriorations * 0.15)
    
    final_score = (classification_score * 0.4) + (queue_score * 0.4) + (speed_score * 0.2) - penalty
    return max(0.0, min(1.0, final_score))

def get_task_2_breakdown(env_state: EnvState, patient_hidden_states: dict, patient_observations: dict, final_queue: list[str]) -> dict:
    """Provides a detailed diagnostic breakdown of the Task 2 scores."""
    classification_score = env_state.stats.correct_classifications / 10.0
    optimal_queue = calculate_optimal_queue(patient_hidden_states, patient_observations, final_queue)
    queue_score = get_queue_score(final_queue, optimal_queue)
    speed_score = max(0.0, 1.0 - (env_state.stats.total_steps / settings.MAX_STEPS))
    penalty = (env_state.stats.invalid_actions * 0.05) + (env_state.stats.preventable_deteriorations * 0.15)
    
    final_score = (classification_score * 0.4) + (queue_score * 0.4) + (speed_score * 0.2) - penalty
    
    return {
        "classification_score": classification_score,
        "queue_score": queue_score,
        "speed_score": speed_score,
        "penalty": penalty,
        "final_score": max(0.0, min(1.0, final_score))
    }
