# triage_env/app/core/constants/thresholds.py

# Per-step vital sign decay rates for patients waiting without assigned treatment
VITAL_DETERIORATION_RATES = {
    "spo2": -2,
    "heart_rate": 10,
    "systolic_bp": -5,
    "respiratory_rate": 2,
    "gcs": -1  # Note: Logic must restrict GCS decay to ESI 1 and 2 only
}

# Calculated starting vitals for synthetic patient generation based on clinical severity
ESI_BASELINE_VITALS = {
    1: {"spo2": 65, "heart_rate": 160, "systolic_bp": 70, "respiratory_rate": 30, "temperature": 39.0, "gcs": 3},
    2: {"spo2": 88, "heart_rate": 155, "systolic_bp": 78, "respiratory_rate": 28, "temperature": 38.8, "gcs": 12},
    3: {"spo2": 92, "heart_rate": 110, "systolic_bp": 100, "respiratory_rate": 22, "temperature": 38.0, "gcs": 15},
    4: {"spo2": 96, "heart_rate": 80, "systolic_bp": 120, "respiratory_rate": 16, "temperature": 37.0, "gcs": 15},
    5: {"spo2": 98, "heart_rate": 72, "systolic_bp": 115, "respiratory_rate": 14, "temperature": 36.6, "gcs": 15}
}

# The percentage variance (±) applied to baseline vitals during the synthetic generation process
VITAL_GENERATION_VARIANCE = 0.10

# Absolute physiological danger values that trigger status changes in the status manager
CRITICAL_VITAL_THRESHOLDS = {
    "spo2_min": 70,
    "heart_rate_max": 160,
    "heart_rate_min": 40,
    "systolic_bp_min": 70,
    "gcs_min": 3
}

# Hard time-limits in simulation steps for unassigned patients before the episode fails
MAX_UNASSIGNED_STEPS_BEFORE_TERMINATION = {
    1: 6,     # 30 mins
    2: 10,    # 50 mins
    3: 20,    # 100 mins
    4: None,  # No hard limit
    5: None   # No hard limit
}
