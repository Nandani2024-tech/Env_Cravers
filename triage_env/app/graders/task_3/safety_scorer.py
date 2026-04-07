# triage_env/app/graders/task_3/safety_scorer.py
from app.core.models.environment import EnvState

def score_safety(env_state: EnvState, total_patients: int) -> float:
    """Computes a safety-focused score by penalizing clinical deteriorations and invalid actions."""
    deteriorations = env_state.stats.preventable_deteriorations
    invalid = env_state.stats.invalid_actions
    
    # Significant deduction (20%) for each preventable patient deterioration
    deterioration_penalty = deteriorations * 0.2
    
    # Minor deduction (5%) for each unsupported agent action
    invalid_penalty = invalid * 0.05
    
    raw = 1.0 - deterioration_penalty - invalid_penalty
    return max(0.0, min(1.0, raw))

def get_task_3_final_score(resource_score: float, time_score: float, safety_score: float) -> float:
    """Assembles all Task 3 subscores into a single weighted performance metric (0.0 to 1.0)."""
    # 40% matching correctness, 30% time management, 30% absolute patient safety
    final = (resource_score * 0.4) + (time_score * 0.3) + (safety_score * 0.3)
    return max(0.0, min(1.0, final))
