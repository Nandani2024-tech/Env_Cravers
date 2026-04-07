# triage_env/app/data/scenario_builder.py
import random
from app.core.seeds import apply_seed, TASK_SEEDS
from app.core.models.observation import PatientObservation
from app.core.models.environment import PatientHiddenState
from app.data.patient_factory import generate_patient

TASK_ESI_DISTRIBUTIONS = {
    "task_1": [None],  # ESI chosen randomly per episode, single patient
    "task_2": [1, 2, 2, 3, 3, 3, 4, 4, 5, 5],  # 10 patients, weighted toward middle
    "task_3": [1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5]  # 15 patients, full spread
}

def _build_scenario(esi_list: list, shuffle_queue: bool) -> tuple[dict[str, PatientObservation], dict[str, PatientHiddenState], list[str]]:
    """Generates patients from an ESI distribution and returns initialized environment state components."""
    observations = {}
    hidden_states = {}
    queue = []
    
    for i, esi in enumerate(esi_list):
        # Task 1 uses a random ESI level; Tasks 2/3 use predefined distributions
        actual_esi = random.randint(1, 5) if esi is None else esi
        
        obs, hidden = generate_patient(actual_esi, i + 1)
        observations[obs.patient_id] = obs
        hidden_states[obs.patient_id] = hidden
        queue.append(obs.patient_id)
        
    if shuffle_queue:
        random.shuffle(queue)
        
    return observations, hidden_states, queue

def build_task_1_scenario() -> tuple[dict[str, PatientObservation], dict[str, PatientHiddenState], list[str]]:
    """Builds a single-patient classification scenario (Task 1)."""
    apply_seed("task_1")
    return _build_scenario(TASK_ESI_DISTRIBUTIONS["task_1"], shuffle_queue=False)

def build_task_2_scenario() -> tuple[dict[str, PatientObservation], dict[str, PatientHiddenState], list[str]]:
    """Builds a 10-patient queue management scenario (Task 2)."""
    apply_seed("task_2")
    return _build_scenario(TASK_ESI_DISTRIBUTIONS["task_2"], shuffle_queue=True)

def build_task_3_scenario() -> tuple[dict[str, PatientObservation], dict[str, PatientHiddenState], list[str]]:
    """Builds a full ER management scenario with 15 patients (Task 3)."""
    apply_seed("task_3")
    return _build_scenario(TASK_ESI_DISTRIBUTIONS["task_3"], shuffle_queue=True)
