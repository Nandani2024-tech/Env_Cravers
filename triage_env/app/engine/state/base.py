# triage_env/app/engine/state/base.py
from abc import ABC, abstractmethod
from app.core.models.environment import EnvState
from app.core.models.observation import TriageObservation

class BaseStateTracker(ABC):
    """Abstract interface defining the simulation state management lifecycle."""
    
    @abstractmethod
    def initialize(self, task_id: str, patient_observations: dict, patient_hidden_states: dict, initial_queue: list) -> EnvState:
        """Initialize fresh EnvState for a new episode."""
        pass
    
    @abstractmethod
    def update_after_step(self, env_state: EnvState, patient_observations: dict, patient_hidden_states: dict, discharged_this_step: list) -> EnvState:
        """Apply all per-step state mutations."""
        pass

    @abstractmethod
    def get_teacher_view(self, env_state: EnvState) -> dict:
        """Return the full hidden state as a serializable dict."""
        pass

    @abstractmethod
    def build_observation(self, env_state: EnvState, patient_observations: dict, task_id: str) -> TriageObservation:
        """Construct the agent-facing observation from current state."""
        pass
