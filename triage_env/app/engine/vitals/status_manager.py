# triage_env/app/engine/vitals/status_manager.py
from app.core.models.observation import VitalSigns, PatientObservation
from app.engine.vitals.calculator import STABLE_MIDPOINTS

# Clinical thresholds defining the minimum shift required for medical significance
SIGNIFICANCE_THRESHOLDS = {
    "spo2": 3,
    "heart_rate": 10,
    "systolic_bp": 10,
    "temperature": 0.5,
    "respiratory_rate": 3,
    "gcs": 1
}

def _is_clinically_significant(vital_name: str, old_val: float, new_val: float) -> bool:
    """Checks if a vital sign shift exceeds medically meaningful thresholds."""
    if vital_name not in SIGNIFICANCE_THRESHOLDS:
        return False
    return abs(new_val - old_val) >= SIGNIFICANCE_THRESHOLDS[vital_name]

def _determine_change_type(old_vitals: VitalSigns, new_vitals: VitalSigns) -> str:
    """Categorizes clinical progression based on proximity movement toward stable midpoints."""
    away_count = 0
    toward_count = 0
    old_dict = old_vitals.model_dump()
    new_dict = new_vitals.model_dump()

    for key, midpoint in STABLE_MIDPOINTS.items():
        if key not in old_dict or key not in new_dict:
            continue
        old_dist = abs(old_dict[key] - midpoint)
        new_dist = abs(new_dict[key] - midpoint)
        
        if new_dist > old_dist:
            away_count += 1
        elif new_dist < old_dist:
            toward_count += 1

    if away_count > toward_count:
        return "deteriorated"
    if toward_count > away_count:
        return "improved"
    return "stable"

def get_status_update(old_vitals: VitalSigns, new_vitals: VitalSigns, patient: PatientObservation) -> PatientObservation:
    """Analyzes vital shifts and populates status-change flags in the patient observation object."""
    changed_vitals = []
    old_dict = old_vitals.model_dump()
    new_dict = new_vitals.model_dump()
    
    # Identify significant shifts across all monitored vitals
    for vital_name in SIGNIFICANCE_THRESHOLDS.keys():
        if _is_clinically_significant(vital_name, old_dict.get(vital_name, 0), new_dict.get(vital_name, 0)):
            changed_vitals.append(vital_name)

    # Generate updated observation with current vitals and status flags
    status_changed = len(changed_vitals) > 0
    change_type = _determine_change_type(old_vitals, new_vitals) if status_changed else "stable"

    return patient.model_copy(update={
        "vitals": new_vitals,
        "status_changed": status_changed,
        "change_type": change_type,
        "changed_vitals": changed_vitals
    })
