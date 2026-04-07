# triage_env/app/core/models/observation.py
from typing import Optional
from pydantic import BaseModel, Field

class VitalSigns(BaseModel):
    """Numerical physiological measurements for a patient."""
    heart_rate: int # Beats per minute
    systolic_bp: int # Systolic blood pressure (mmHg)
    diastolic_bp: int # Diastolic blood pressure (mmHg)
    temperature: float # Body temperature (Celsius)
    spo2: int # Oxygen saturation (%)
    respiratory_rate: int # Breaths per minute
    gcs: int # Glasgow Coma Scale (3-15)

class MedicalHistory(BaseModel):
    """Hidden health records unlocked by request_info action."""
    prior_er_visits: int # Count of previous emergency room admissions
    chronic_conditions: list[str] # Known long-term illnesses
    current_medications: list[str] # Medications the patient is taking
    allergies: list[str] # List of drug or environmental allergies

class PatientObservation(BaseModel):
    """Snapshot of a single patient's state as perceived by the agent."""
    patient_id: str # Unique identifier for the patient
    age: int # Patient age in years
    gender: str # Biological gender
    chief_complaint: str # The primary reason for clinical visit
    symptoms: list[str] # List of current symptomatic complaints
    vitals: VitalSigns # Current physiological measurements
    esi_level_assigned: Optional[int] = None # Agent-assigned ESI level (1-5)
    assigned_resource: Optional[str] = None # Resource ID if patient is admitted
    wait_steps: int # Total simulation steps spent in queue
    status_changed: bool # True if vitals shifted this step
    change_type: Optional[str] = None # "deteriorated", "improved", or "stable"
    changed_vitals: list[str] = Field(default_factory=list) # Names of vitals that shifted
    hidden_history: Optional[MedicalHistory] = None # Populated after request_info

class ResourceObservation(BaseModel):
    """State of a physical ER resource (bed, bay, or doctor)."""
    resource_id: str # Unique identifier for the resource
    resource_type: str # Monitored, General, Trauma, Doctor, or Discharge
    is_occupied: bool # True if a patient is currently assigned
    occupied_by: Optional[str] = None # Patient ID currently in the resource
    steps_until_free: Optional[int] = None # Countdown until auto-release

class TriageObservation(BaseModel):
    """Complete environment observation payload per step."""
    task_id: str # Current simulation task identifier
    current_step: int # Current step in the 30-step episode
    elapsed_minutes: int # Simulation clock (current_step * 5)
    patients: list[PatientObservation] # All patients in the scenario
    resources: list[ResourceObservation] # All resources in the scenario
    queue_order: list[str] # Priority-ordered list of waiting patient IDs
    episode_done: bool # Termination flag
    info: dict = Field(default_factory=dict) # Optional clinical metadata
