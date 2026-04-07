# triage_env/app/core/constants/resources.py

# Unique identifiers for the available trauma units in the ER
TRAUMA_BAY_IDS = ["trauma_bay"]

# Unique identifiers for all patient beds in the ER
BED_IDS = ["bed_1", "bed_2", "bed_3"]

# Unique identifiers for the assigned ER physicians
DOCTOR_IDS = ["doctor_1", "doctor_2"]

# Capability-based categorization for each bed in the ER
BED_TYPES = {
    "bed_1": "Monitored",
    "bed_2": "Monitored",
    "bed_3": "General"
}

# Identifier for the non-resource zone where Level 5 patients are managed
DISCHARGE_AREA_ID = "discharge_area"

# Reference of the total available resource counts in the environment
TOTAL_CAPACITY = {
    "trauma_bays": 1,
    "beds": 3,
    "doctors": 2
}

# Complete flat list of all assignable resource IDs in the environment
ALL_RESOURCE_IDS = TRAUMA_BAY_IDS + BED_IDS + DOCTOR_IDS + [DISCHARGE_AREA_ID]

# Clinical compatibility matrix mapping ESI levels to necessary locations and staffing
ESI_COMPATIBILITY_MATRIX = {
    1: {
        "valid_locations": ["trauma_bay"],
        "requires_doctor": True
    },
    2: {
        "valid_locations": ["trauma_bay", "bed_1", "bed_2"],
        "requires_doctor": True
    },
    3: {
        "valid_locations": ["bed_1", "bed_2", "bed_3"],
        "requires_doctor": True
    },
    4: {
        "valid_locations": ["bed_3"],
        "requires_doctor": False
    },
    5: {
        "valid_locations": ["discharge_area"],
        "requires_doctor": False
    }
}
