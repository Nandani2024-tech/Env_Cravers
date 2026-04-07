# triage_env/app/core/constants/protocols.py

# Mapping of ESI levels to their official clinical priority labels
ESI_LEVEL_DEFINITIONS = {
    1: "Immediate",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent"
}

# Physiological ranges defining a clinically 'stable' patient
STABLE_VITALS_RANGE = {
    "spo2": (94, 100),  # Oxygen saturation above 94%
    "heart_rate": (40, 100),
    "systolic_bp": (90, 180),
    "temperature": (36.0, 38.5),
    "respiratory_rate": (12, 20),
    "gcs": (15, 15)
}

# Specific conditions and physiological triggers for ESI Level 1 (Resuscitation)
ESI_LEVEL_1_CRITERIA = [
    "cardiac_arrest",
    "respiratory_arrest",
    "unresponsive",
    "no_pulse",
    "spo2_below_70",
    "gcs_3"
]

# Specific conditions and physiological triggers for ESI Level 2 (Emergent)
ESI_LEVEL_2_CRITERIA = [
    "spo2_below_90",
    "heart_rate_above_150",
    "heart_rate_below_40",
    "systolic_bp_below_80",
    "severe_pain_9_10",
    "altered_mental_status",
    "stroke_symptoms",
    "anaphylaxis"
]

# Reward weights for Task 1 classification accuracy based on level distance
TASK_1_SCORING_VALUES = {
    0: 1.0,  # Exact match
    1: 0.6,  # Off by 1 level
    2: 0.2,  # Off by 2 levels
    3: 0.0,  # Off by 3 or more levels
    4: 0.0   # Off by 3 or more levels
}

# Number of 5-minute simulation steps required for automated treatment release per ESI level
ESI_PROCESSING_TIMES = {
    1: 6,  # 30 mins
    2: 5,  # 25 mins
    3: 4,  # 20 mins
    4: 2,  # 10 mins
    5: 1   # 5 mins
}

# The complete list of valid hospital resources recognized by the environment
RESOURCE_DEFINITIONS = [
    "Labs",
    "ECG",
    "IV Fluids",
    "Imaging",
    "Specialist Consultation",
    "Wound Care",
    "Urinalysis",
    "Medication Administration"
]
