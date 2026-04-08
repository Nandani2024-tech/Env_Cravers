# triage_env/app/tasks/base_task.py
from abc import ABC, abstractmethod
from typing import Optional
from app.core.models.action import TriageAction
from app.core.models.environment import EnvState, PatientHiddenState, Reward, StepResult
from app.core.models.observation import TriageObservation, PatientObservation
from app.core.validator import ActionValidator
from app.engine.state.registry import StateRegistry
from app.engine.termination import TerminationEngine

class BaseScenario(ABC):
    """Abstract base class establishing the contract and shared logic for all triage scenario tasks."""

    def __init__(self):
        self.env_state: Optional[EnvState] = None
        self.patient_observations: dict[str, PatientObservation] = {}
        self.patient_hidden_states: dict[str, PatientHiddenState] = {}
        self.state_registry = StateRegistry()
        self.validator = ActionValidator()
        self.termination_engine = TerminationEngine()

    @abstractmethod
    def initialize(self) -> tuple[TriageObservation, EnvState]:
        """Set up episode, return first observation and initial state."""
        pass

    @abstractmethod
    def step(self, action: TriageAction) -> StepResult:
        """Process one agent action, return StepResult."""
        pass

    @abstractmethod
    def get_state(self) -> dict:
        """Return full teacher view."""
        pass

    @abstractmethod
    def get_final_score(self) -> tuple[float, dict]:
        """Return normalized episode score 0.0-1.0 and details."""
        pass

    def _handle_invalid_action(self, reason: str) -> StepResult:
        """Shared logic for when the validator rejects an action."""
        self.env_state.stats.invalid_actions += 1
        self.env_state.stats.total_reward -= 0.2
        obs = self._build_current_observation()
        return StepResult(
            observation=obs, 
            reward=Reward(value=-0.2),
            done=False, 
            info={
                "error": reason,
                "reward_breakdown": {
                    "action_reward": 0.0,
                    "invalid_action_penalty": -0.2,
                    "deterioration_penalty": 0.0,
                    "time_bonus": 0.0
                }
            }
        )

    def _build_current_observation(self) -> TriageObservation:
        """Constructs the agent-facing observation from current state."""
        return self.state_registry.build_observation(self.env_state, self.patient_observations, self.env_state.task_id)
