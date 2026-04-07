# triage_env/app/graders/task_3/resource_scorer.py
from app.core.models.environment import EnvState

def score_resource_assignments(assigned_correctly: int, assigned_incorrectly: int, total_patients: int) -> float:
    """Calculates the accuracy score for resource-to-patient alignment (0.0 to 1.0)."""
    # Simply calculates the ratio of perfectly matched assignments against the task population
    return assigned_correctly / max(1, total_patients)
