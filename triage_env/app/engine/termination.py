# triage_env/app/engine/termination.py
from typing import Optional
from app.core.config import settings
from app.core.constants.thresholds import MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION
from app.core.models.environment import EnvState, PatientHiddenState
from app.core.models.observation import PatientObservation

class TerminationEngine:
    """Monitors simulation safety boundaries and manages episode termination rules."""

    def check_termination(
        self,
        env_state: EnvState,
        patient_hidden_states: dict[str, PatientHiddenState],
        patient_observations: dict[str, PatientObservation]
    ) -> tuple[bool, Optional[str]]:
        """Evaluates all termination criteria sequentially to decide if the episode continues."""
        max_steps_done, max_steps_reason = self._check_max_steps(env_state)
        if max_steps_done:
            return True, max_steps_reason

        critical_done, critical_reason = self._check_critical_patient_timeout(
            env_state, patient_hidden_states, patient_observations
        )
        if critical_done:
            return True, critical_reason

        return False, None

    def decrement_deterioration_counters(self, env_state: EnvState) -> list[str]:
        """Decrements critical clinical timers for unassigned patients and flags preventable deterioration."""
        deteriorated_patients = []
        for pid, hidden_state in env_state.patient_hidden_states.items():
            if pid not in env_state.optimal_queue_order:
                continue # Only decrement counters for patients currently unassigned
                
            if hidden_state.steps_until_deterioration is not None:
                hidden_state.steps_until_deterioration -= 1
                if hidden_state.steps_until_deterioration == 0:
                    hidden_state.preventable_deterioration_occurred = True
                    env_state.stats.preventable_deteriorations += 1
                    deteriorated_patients.append(pid)
        return deteriorated_patients

    def _check_max_steps(self, env_state: EnvState) -> tuple[bool, Optional[str]]:
        """Checks if the episode has exhausted the configured maximum allowed steps."""
        if env_state.current_step >= settings.MAX_STEPS:
            return True, "Maximum steps reached"
        return False, None

    def _check_critical_patient_timeout(
        self,
        env_state: EnvState,
        patient_hidden_states: dict[str, PatientHiddenState],
        patient_observations: dict[str, PatientObservation]
    ) -> tuple[bool, Optional[str]]:
        """Terminates if any critically ill unassigned patient waits beyond the medical safety threshold."""
        for pid in env_state.optimal_queue_order:
            if pid not in patient_hidden_states or pid not in patient_observations:
                continue
                
            hidden = patient_hidden_states[pid]
            obs = patient_observations[pid]
            
            limit = MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION.get(hidden.true_esi_level)
            if limit is not None and obs.wait_steps > limit:
                return True, f"Preventable deterioration: Patient {pid} (ESI {hidden.true_esi_level}) waited {obs.wait_steps} steps without assignment"
                
        return False, None
