# triage_env/app/utils/formatters.py

def format_patient_summary(patient_id: str, esi_level: int, wait_steps: int) -> str:
    """Returns a clean one-line string for logging: [P-001 | ESI-2 | Wait: 3 steps]."""
    return f"[{patient_id} | ESI-{esi_level} | Wait: {wait_steps} steps]"

def format_step_log(step: int, action_type: str, reward: float, done: bool) -> str:
    """Returns formatted step log matching the [STEP] format: [STEP] step=1 action=classify reward=0.80 done=false."""
    return f"[STEP] step={step} action={action_type.lower()} reward={reward:.2f} done={str(done).lower()}"
