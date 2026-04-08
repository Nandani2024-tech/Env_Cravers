# triage_env/app/core/models/environment.py
from typing import Optional
from pydantic import BaseModel, Field
from app.core.models.observation import TriageObservation, MedicalHistory
from app.core.models.action import TriageAction

class PatientHiddenState(BaseModel):
    """Hidden ground truth for a single patient in the simulation."""
    true_esi_level: int # The actual ESI priority baseline
    steps_until_deterioration: Optional[int] = None # Steps before next vital drop
    medical_history: MedicalHistory # Complete history revealed on request_info
    history_unlocked: bool = False # Flag showing if history was retrieved
    optimal_resource: Optional[str] = None # Medically correct resource ID
    preventable_deterioration_occurred: bool = False # Safety failure flag

class EpisodeStats(BaseModel):
    """Running performance statistics for a simulation episode."""
    total_steps: int = 0 # Elapsed steps in current episode
    preventable_deteriorations: int = 0 # Count of avoidable clinical failures
    correct_classifications: int = 0 # Count of accurate ESI assignments
    incorrect_classifications: int = 0 # Count of inaccurate ESI assignments
    invalid_actions: int = 0 # Count of rejected agent actions
    request_info_uses: int = 0 # Count of info retrieval calls
    total_reward: float = 0.0 # Aggregated episodic score

class EnvState(BaseModel):
    """Full internal environment state (Teacher View)."""
    task_id: str # Identifier for the active scenario
    current_step: int = 0 # Current step in the episode
    patient_hidden_states: dict[str, PatientHiddenState] = Field(default_factory=dict) # Map of IDs to hidden truths
    optimal_queue_order: list[str] = Field(default_factory=list) # Correct priority sequence
    resource_occupancy: dict[str, Optional[str]] = Field(default_factory=dict) # resource_id -> patient_id map
    resource_release_countdowns: dict[str, Optional[int]] = Field(default_factory=dict) # resource_id -> steps_spent
    stats: EpisodeStats = Field(default_factory=EpisodeStats) # Episode performance tracker
    episode_done: bool = False # Termination status
    termination_reason: Optional[str] = None # Human-readable cause of episode end

class Reward(BaseModel):
    """OpenEnv standard typed reward model."""
    value: float

class StepResult(BaseModel):
    """OpenEnv standard return object for environment step() calls."""
    observation: TriageObservation # Agent's view of the next state
    reward: Reward # Step-specific reward signal
    done: bool # Episode termination flag
    info: dict = Field(default_factory=dict) # Additional clinical metadata

# OpenEnv Compatibility Aliases (placed centrally for validator discovery)
Observation = TriageObservation
Action = TriageAction
