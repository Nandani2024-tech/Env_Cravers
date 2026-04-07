# triage_env/app/core/seeds.py
import random
import numpy as np

# Fixed random seeds for each task type to ensure simulation reproducibility
TASK_SEEDS = {
    "task_1": 42,
    "task_2": 2024,
    "task_3": 999,
    "global": 1
}

def apply_seed(task_id: str) -> None:
    """
    Applies the fixed random seed for a specific task to random and numpy.
    
    Valid task_id values are: 'task_1', 'task_2', 'task_3', or 'global'.
    
    Args:
        task_id: The identifier for the current scenario.
    
    Raises:
        ValueError: If the task_id is not found in TASK_SEEDS.
    """
    if task_id not in TASK_SEEDS:
        valid_tasks = ", ".join(TASK_SEEDS.keys())
        raise ValueError(f"Invalid task_id '{task_id}'. Valid IDs are: {valid_tasks}")
    
    seed_value = TASK_SEEDS[task_id]
    random.seed(seed_value)
    np.random.seed(seed_value)
