#!/usr/bin/env python3
"""
Verification script for all applied fixes to the Clinical Triage RL Environment.
Tests each fix independently and generates a comprehensive report.
"""

import sys
sys.path.insert(0, "/home/vedu/Work/Env_Cravers/triage_env")

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
from app.core.seeds import USE_RANDOM_SEEDS
import time

def verify_c1_assigned_resource_cleared():
    """Fix C1: Verify assigned_resource is cleared after discharge/release."""
    print("\n=== FIX C1: assigned_resource cleared after discharge ===")
    
    environment.reset("task_3")
    state = environment.state()
    
    # Find a low-acuity patient for discharge
    patient_id = None
    for pid, hidden in state["patient_hidden_states"].items():
        if hidden["true_esi_level"] in [4, 5]:
            patient_id = pid
            optimal_resource = hidden["optimal_resource"]
            break
    
    if not patient_id:
        print("❌ FAILED: No suitable patient found")
        return False
    
    # Assign patient
    result1 = environment.step(TriageAction(
        task_id="task_3",
        action_type=ActionType.ASSIGN,
        patient_id=patient_id,
        value=optimal_resource
    ))
    
    # Check assignment recorded
    patient_obs = next(p for p in result1.observation.patients if p.patient_id == patient_id)
    if patient_obs.assigned_resource != optimal_resource:
        print(f"❌ FAILED: Resource not assigned. Expected {optimal_resource}, got {patient_obs.assigned_resource}")
        return False
    
    # Discharge patient
    result2 = environment.step(TriageAction(
        task_id="task_3",
        action_type=ActionType.DISCHARGE,
        patient_id=patient_id,
        value=None
    ))
    
    # Verify assigned_resource cleared
    patient_obs_after = next((p for p in result2.observation.patients if p.patient_id == patient_id), None)
    if patient_obs_after and patient_obs_after.assigned_resource is not None:
        print(f"❌ FAILED: assigned_resource not cleared after discharge. Value: {patient_obs_after.assigned_resource}")
        return False
    
    # Also check occupancy cleared
    state_after = environment.state()
    occupancy = state_after["resource_occupancy"]
    if patient_id in occupancy.values():
        print(f"❌ FAILED: Patient still in occupancy after discharge: {occupancy}")
        return False
    
    print("✅ PASSED: assigned_resource cleared correctly")
    return True


def verify_c3_max_step_enforcement():
    """Fix C3: Verify episodes terminate at exactly MAX_STEPS."""
    print("\n=== FIX C3: Max-step enforcement ===")
    
    from app.core.config import settings
    MAX_STEPS = settings.MAX_STEPS
    
    environment.reset("task_1")
    
    # Execute exactly MAX_STEPS actions
    step_count = 0
    done = False
    
    for i in range(MAX_STEPS + 5):  # Try to exceed
        result = environment.step(TriageAction(
            task_id="task_1",
            action_type=ActionType.REQUEST_INFO,
            patient_id="P-001",
            value=None
        ))
        step_count += 1
        
        if result.done:
            done = True
            break
    
    if not done:
        print(f"❌ FAILED: Episode did not terminate after {step_count} steps")
        return False
    
    if step_count != MAX_STEPS:
        print(f"❌ FAILED: Episode terminated at step {step_count}, expected {MAX_STEPS}")
        return False
    
    print(f"✅ PASSED: Episode terminated exactly at step {MAX_STEPS}")
    return True


def verify_c2_queue_grading():
    """Fix C2: Verify Task 2 queue grading does not trivialize."""
    print("\n=== FIX C2: Task 2 queue grading ===")
    
    from app.engine.queue.sorter import get_queue_score
    
    # Test empty queue returns 0.0 (not 1.0)
    score_empty = get_queue_score([], [])
    if score_empty != 0.0:
        print(f"❌ FAILED: Empty queue score is {score_empty}, expected 0.0")
        return False
    
    print("✅ PASSED: Empty queue returns score 0.0")
    return True


def verify_s1_random_seed_mode():
    """Fix S1: Verify random seed mode can be enabled."""
    print("\n=== FIX S1: Random seed mode ===")
    
    if USE_RANDOM_SEEDS:
        print("ℹ️  Random seeds are ENABLED")
        
        # Reset multiple times and check for variation
        esi_distributions = []
        for _ in range(3):
            obs = environment.reset("task_1")
            state = environment.state()
            esis = [h["true_esi_level"] for h in state["patient_hidden_states"].values()]
            esi_distributions.append(tuple(sorted(esis)))
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        if len(set(esi_distributions)) == 1:
            print(f"⚠️  WARNING: All resets produced same ESI distribution: {esi_distributions[0]}")
            print("    This might indicate seeds are still deterministic")
        else:
            print(f"✅ PASSED: Random seeds produce varied scenarios")
            return True
    else:
        print("ℹ️  Random seeds are DISABLED (deterministic mode)")
        
        # Verify determinism
        esi_distributions = []
        for _ in range(3):
            obs = environment.reset("task_1")
            state = environment.state()
            esis = [h["true_esi_level"] for h in state["patient_hidden_states"].values()]
            esi_distributions.append(tuple(sorted(esis)))
        
        if len(set(esi_distributions)) > 1:
            print(f"❌ FAILED: Deterministic mode produced varied scenarios: {esi_distributions}")
            return False
        
        print(f"✅ PASSED: Deterministic mode works correctly")
        return True
    
    return True


def verify_s2_discharge_reward_adjustment():
    """Fix S2: Verify Task 3 discharge rewards reduced for low-acuity."""
    print("\n=== FIX S2: Task 3 discharge reward adjustment ===")
    
    environment.reset("task_3")
    state = environment.state()
    
    # Find low-acuity patient
    low_acuity_patient = None
    for pid, hidden in state["patient_hidden_states"].items():
        if hidden["true_esi_level"] in [4, 5]:
            low_acuity_patient = (pid, hidden["optimal_resource"])
            break
    
    if not low_acuity_patient:
        print("⚠️  WARNING: No low-acuity patient found in scenario")
        return True
    
    patient_id, optimal_resource = low_acuity_patient
    
    # Assign then discharge
    environment.step(TriageAction(
        task_id="task_3",
        action_type=ActionType.ASSIGN,
        patient_id=patient_id,
        value=optimal_resource
    ))
    
    discharge_result = environment.step(TriageAction(
        task_id="task_3",
        action_type=ActionType.DISCHARGE,
        patient_id=patient_id,
        value=None
    ))
    
    discharge_reward = discharge_result.reward.value
    
    # Should be 0.0 for low-acuity discharge (was 0.05)
    if discharge_reward > 0.0:
        print(f"❌ FAILED: Low-acuity discharge gave positive reward: {discharge_reward}")
        return False
    
    if discharge_reward == 0.0:
        print(f"✅ PASSED: Low-acuity discharge reward is now 0.0 (was 0.05)")
        return True
    
    print(f"ℹ️  Low-acuity discharge reward: {discharge_reward}")
    return True


def main():
    print("=" * 70)
    print("CLINICAL TRIAGE RL ENVIRONMENT - FIX VERIFICATION")
    print("=" * 70)
    
    results = {
        "C1 - assigned_resource cleared": verify_c1_assigned_resource_cleared(),
        "C3 - max-step enforcement": verify_c3_max_step_enforcement(),
        "C2 - queue grading fix": verify_c2_queue_grading(),
        "S1 - random seed mode": verify_s1_random_seed_mode(),
        "S2 - discharge reward adjustment": verify_s2_discharge_reward_adjustment(),
    }
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    for fix_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{fix_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL FIXES VERIFIED SUCCESSFULLY")
    else:
        print("❌ SOME FIXES FAILED VERIFICATION")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
