from app.environment import environment
from app.core.constants.resources import ESI_COMPATIBILITY_MATRIX
from app.core.models.action import ActionType, TriageAction
from app.core.models.environment import Reward


def _find_patient_in_observation(observation, patient_id: str):
    for patient in observation.patients:
        if patient.patient_id == patient_id:
            return patient
    return None


def test_rejects_cross_task_actions():
    obs = environment.reset("task_1")
    patient_id = obs.patients[0].patient_id

    result = environment.step(
        TriageAction(
            task_id="task_2",
            action_type=ActionType.CLASSIFY,
            patient_id=patient_id,
            value=3,
        )
    )

    assert result.reward.value == -0.2
    assert "does not match active task" in result.info.get("error", "")


def test_task2_classification_removes_patient_from_queue():
    environment.reset("task_2")
    state = environment.state()
    patient_id = state["optimal_queue_order"][0]
    true_esi = state["patient_hidden_states"][patient_id]["true_esi_level"]

    result = environment.step(
        TriageAction(
            task_id="task_2",
            action_type=ActionType.CLASSIFY,
            patient_id=patient_id,
            value=true_esi,
        )
    )

    assert patient_id not in result.observation.queue_order
    patient = _find_patient_in_observation(result.observation, patient_id)
    assert patient is not None
    assert patient.esi_level_assigned == true_esi


def test_task3_assignment_removes_patient_from_queue_and_marks_resource():
    environment.reset("task_3")
    state = environment.state()
    patient_id = state["optimal_queue_order"][0]
    optimal_resource = state["patient_hidden_states"][patient_id]["optimal_resource"]

    result = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )

    assert patient_id not in result.observation.queue_order
    patient = _find_patient_in_observation(result.observation, patient_id)
    assert patient is not None
    assert patient.assigned_resource == optimal_resource
    assert result.reward.value > 0


def test_task3_invalid_assign_does_not_crash():
    environment.reset("task_3")

    result = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id="P-999",
            value="bed_1",
        )
    )

    assert result.reward.value == -0.2
    assert "not found" in result.info.get("error", "")


def test_task3_correct_assignment_beats_suboptimal_assignment():
    environment.reset("task_3")
    state = environment.state()

    selected_patient = None
    for patient_id, hidden in state["patient_hidden_states"].items():
        esi = hidden["true_esi_level"]
        valid_locations = ESI_COMPATIBILITY_MATRIX[esi]["valid_locations"]
        if esi == 3 and len(valid_locations) > 1:
            selected_patient = (
                patient_id,
                hidden["optimal_resource"],
                next(loc for loc in valid_locations if loc != hidden["optimal_resource"]),
            )
            break

    assert selected_patient is not None
    patient_id, optimal_resource, suboptimal_resource = selected_patient

    correct_result = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )

    environment.reset("task_3")
    suboptimal_result = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=suboptimal_resource,
        )
    )

    assert correct_result.reward.value > suboptimal_result.reward.value


def test_task3_prevents_second_assignment_for_same_patient():
    environment.reset("task_3")
    state = environment.state()
    patient_id = state["optimal_queue_order"][0]
    optimal_resource = state["patient_hidden_states"][patient_id]["optimal_resource"]

    first = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )
    second = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )

    assert first.reward.value > 0
    assert second.reward.value == -0.2
    assert "cannot be assigned again" in second.info.get("error", "")


def test_task3_prevents_reassign_after_discharge():
    environment.reset("task_3")
    state = environment.state()

    candidate = None
    for patient_id in state["optimal_queue_order"]:
        hidden = state["patient_hidden_states"][patient_id]
        if hidden["true_esi_level"] in (4, 5):
            candidate = (patient_id, hidden["optimal_resource"])
            break
    assert candidate is not None
    patient_id, optimal_resource = candidate

    assigned = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )
    discharged = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.DISCHARGE,
            patient_id=patient_id,
            value=None,
        )
    )
    reassigned = environment.step(
        TriageAction(
            task_id="task_3",
            action_type=ActionType.ASSIGN,
            patient_id=patient_id,
            value=optimal_resource,
        )
    )

    assert assigned.reward.value > 0
    assert discharged.reward.value >= -0.3
    assert reassigned.reward.value == -0.2
    assert "cannot be assigned again" in reassigned.info.get("error", "")
