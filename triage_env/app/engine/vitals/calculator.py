# triage_env/app/engine/vitals/calculator.py
import numpy as np
from app.core.constants.thresholds import VITAL_DETERIORATION_RATES
from app.core.models.observation import VitalSigns

# The baseline 'perfect' vitals used as the target toward which treated patients recover
STABLE_MIDPOINTS = {
    "spo2": 97,
    "heart_rate": 70,
    "systolic_bp": 120,
    "temperature": 37.0,
    "respiratory_rate": 16,
    "gcs": 15
}

def _apply_correlations(vitals: dict, esi_level: int) -> dict:
    """Enforces clinical correlations between related vital signs to ensure medical realism."""
    # Correlation: Low SpO2 triggers compensatory high respiratory rate
    if vitals["spo2"] < 90:
        vitals["respiratory_rate"] += (90 - vitals["spo2"]) * 0.5
    # Correlation: Excessive tachycardia in critical patients signals circulatory shock (lower BP)
    if esi_level <= 2 and vitals["heart_rate"] > 140:
        vitals["systolic_bp"] -= (vitals["heart_rate"] - 140) * 0.3
    # Correlation: Elevated body temperature causes physiological tachycardia
    if vitals["temperature"] > 38.5:
        vitals["heart_rate"] += (vitals["temperature"] - 38.5) * 8
    # Constraint: GCS remains stable (15) for non-critical priority levels 3-5
    if esi_level >= 3:
        vitals["gcs"] = 15
    return vitals

def _clamp_vitals(vitals: dict) -> dict:
    """Clamps all vitals to strictly defined physiological boundaries."""
    vitals["spo2"] = int(np.clip(vitals["spo2"], 0, 100))
    vitals["heart_rate"] = int(np.clip(vitals["heart_rate"], 20, 220))
    vitals["systolic_bp"] = int(np.clip(vitals["systolic_bp"], 50, 250))
    vitals["diastolic_bp"] = int(np.clip(vitals["systolic_bp"] * 0.65, 30, 150))
    vitals["temperature"] = float(np.round(np.clip(vitals["temperature"], 34.0, 42.0), 1))
    vitals["respiratory_rate"] = int(np.clip(vitals["respiratory_rate"], 4, 60))
    vitals["gcs"] = int(np.clip(vitals["gcs"], 3, 15))
    return vitals

def calculate_next_vitals(current_vitals: VitalSigns, esi_level: int, is_treated: bool) -> VitalSigns:
    """Predicts the next step's vitals based on treatment status and deterioration rates."""
    vitals = current_vitals.model_dump()
    
    if is_treated:
        # Conservative recovery: move 5% of the distance toward stable midpoint
        for key, midpoint in STABLE_MIDPOINTS.items():
            if key in vitals:
                vitals[key] += (midpoint - vitals[key]) * 0.05
    else:
        # Deterioration: apply fixed decay rates from protocol thresholds
        for key, rate in VITAL_DETERIORATION_RATES.items():
            if key == "gcs" and esi_level >= 3:
                continue # GCS decay only applies to ESI 1 and 2
            vitals[key] += rate

    # Re-apply clinical rules and boundaries
    vitals = _apply_correlations(vitals, esi_level)
    vitals = _clamp_vitals(vitals)
    
    return VitalSigns(**vitals)
