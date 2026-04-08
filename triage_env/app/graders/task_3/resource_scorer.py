# triage_env/app/graders/task_3/resource_scorer.py
from app.core.models.environment import EnvState

def score_resource_assignments(assigned_correctly: int, assigned_incorrectly: int, total_patients: int) -> float:
    """Scores assignment quality using both precision and coverage (0.0 to 1.0)."""
    attempts = assigned_correctly + assigned_incorrectly
    precision = assigned_correctly / max(1, attempts)
    coverage = assigned_correctly / max(1, total_patients)
    # Precision carries more weight to penalize incorrect assignments.
    score = (precision * 0.7) + (coverage * 0.3)
    return max(0.0, min(1.0, score))
