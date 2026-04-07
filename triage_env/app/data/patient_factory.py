# triage_env/app/data/patient_factory.py
import random
import numpy as np
from app.core.constants.thresholds import ESI_BASELINE_VITALS, VITAL_GENERATION_VARIANCE, MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION
from app.core.constants.resources import ESI_COMPATIBILITY_MATRIX
from app.core.models.observation import VitalSigns, MedicalHistory, PatientObservation
from app.core.models.environment import PatientHiddenState

CHIEF_COMPLAINTS = {
    1: ["Cardiac Arrest", "Respiratory Failure", "Severe Trauma", "Unresponsive"],
    2: ["Chest Pain", "Stroke Symptoms", "Anaphylaxis", "Severe Difficulty Breathing"],
    3: ["Abdominal Pain", "High Fever", "Moderate Fracture", "Dehydration"],
    4: ["Minor Laceration", "Mild Headache", "Sprained Ankle", "Urinary Tract Infection"],
    5: ["Prescription Refill", "Minor Rash", "Cold Symptoms", "Routine Follow-up"]
}

SYMPTOMS_POOL = {
    1: ["no_pulse", "apnea", "unresponsive", "cyanosis", "cardiac_arrest"],
    2: ["severe_chest_pain", "facial_droop", "altered_consciousness", "hives", "stridor"],
    3: ["persistent_vomiting", "high_fever", "moderate_pain", "dizziness", "swelling"],
    4: ["mild_pain", "minor_bleeding", "nausea", "localized_swelling"],
    5: ["runny_nose", "mild_cough", "skin_irritation", "fatigue"]
}

CHRONIC_CONDITIONS_POOL = ["Hypertension", "Diabetes Type 2", "Asthma", "COPD", "Heart Disease", "Kidney Disease", "None"]
MEDICATIONS_POOL = ["Metformin", "Lisinopril", "Atorvastatin", "Albuterol", "Aspirin", "Warfarin", "None"]
ALLERGIES_POOL = ["Penicillin", "Sulfa Drugs", "Ibuprofen", "Latex", "Contrast Dye", "None"]

def generate_vitals(esi_level: int) -> VitalSigns:
    """Generates medically-correlated vitals based on ESI level and baseline thresholds."""
    base = ESI_BASELINE_VITALS[esi_level]
    vitals = {k: np.random.normal(v, v * VITAL_GENERATION_VARIANCE) for k, v in base.items()}
    
    # Correlation: Low SpO2 triggers high respiratory rate
    if vitals["spo2"] < 90:
        vitals["respiratory_rate"] += (90 - vitals["spo2"]) * 0.5
    # Correlation: High HR triggers low systolic BP for critical patients (shock)
    if esi_level <= 2 and vitals["heart_rate"] > 140:
        vitals["systolic_bp"] -= (vitals["heart_rate"] - 140) * 0.3
    # Correlation: Fever elevates heart rate
    if vitals["temperature"] > 38.5:
        vitals["heart_rate"] += (vitals["temperature"] - 38.5) * 8
    # Constraint: GCS stable for levels 3-5
    if esi_level >= 3:
        vitals["gcs"] = 15

    systolic = int(np.clip(vitals["systolic_bp"], 50, 250))
    diastolic = int(np.clip(systolic * 0.65, 30, 150))

    return VitalSigns(
        heart_rate=int(np.clip(vitals["heart_rate"], 20, 220)),
        systolic_bp=systolic,
        diastolic_bp=diastolic,
        temperature=float(np.round(np.clip(vitals["temperature"], 34.0, 42.0), 1)),
        spo2=int(np.clip(vitals["spo2"], 0, 100)),
        respiratory_rate=int(np.clip(vitals["respiratory_rate"], 4, 60)),
        gcs=int(np.clip(vitals["gcs"], 3, 15))
    )

def generate_medical_history(esi_level: int) -> MedicalHistory:
    """Creates a random medical history profile, weighted by clinical severity."""
    prob_none = 0.5 if esi_level >= 3 else 0.1 # Realism: critical patients often have history
    def pick_pool(pool):
        if random.random() < prob_none: return ["None"]
        return random.sample([c for c in pool if c != "None"], k=random.randint(1, 2))

    return MedicalHistory(
        prior_er_visits=random.choices([0, 1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 3, 2])[0],
        chronic_conditions=pick_pool(CHRONIC_CONDITIONS_POOL),
        current_medications=pick_pool(MEDICATIONS_POOL),
        allergies=pick_pool(ALLERGIES_POOL)
    )

def generate_patient(esi_level: int, patient_index: int) -> tuple[PatientObservation, PatientHiddenState]:
    """Orchestrates creation of a synthetic patient profile and their hidden ground truth."""
    patient_id = f"P-{patient_index:03d}"
    vitals = generate_vitals(esi_level)
    history = generate_medical_history(esi_level)
    
    observation = PatientObservation(
        patient_id=patient_id,
        age=random.randint(18, 90),
        gender=random.choice(["Male", "Female"]),
        chief_complaint=random.choice(CHIEF_COMPLAINTS[esi_level]),
        symptoms=random.sample(SYMPTOMS_POOL[esi_level], k=random.randint(2, 3)),
        vitals=vitals,
        wait_steps=0,
        status_changed=False
    )
    hidden_state = PatientHiddenState(
        true_esi_level=esi_level,
        steps_until_deterioration=MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION.get(esi_level),
        medical_history=history,
        optimal_resource=ESI_COMPATIBILITY_MATRIX[esi_level]["valid_locations"][0]
    )
    return observation, hidden_state
