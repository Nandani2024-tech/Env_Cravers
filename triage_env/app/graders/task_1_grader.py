# triage_env/app/graders/task_1_grader.py
from app.core.models.environment import EnvState

def grade_task_1(env_state: EnvState) -> tuple[float, dict]:
    """Calculates the final episode score for Task 1 classification accuracy."""
    details = get_task_1_breakdown(env_state)
    return details["final_score"], details

def get_task_1_breakdown(env_state: EnvState) -> dict:
    """Returns the comprehensive score decomposition for Task 1 logging and feedback."""
    correct = env_state.stats.correct_classifications
    incorrect = env_state.stats.incorrect_classifications
    base_score = correct / max(1, correct + incorrect)
    penalty = env_state.stats.invalid_actions * 0.05
    info_bonus = 0.1 if env_state.stats.request_info_uses > 0 and base_score == 1.0 else 0.0
    
    return {
        "base_score": base_score,
        "penalty": penalty,
        "info_bonus": info_bonus,
        "final_score": 0.01 + 0.98 * max(0.0, min(1.0, base_score - penalty + info_bonus)),
        "correct": correct,
        "incorrect": incorrect,
        "invalid_actions": env_state.stats.invalid_actions
    }
