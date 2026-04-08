# Phase 3 — State Integrity Audit

## Method
Traced all state mutations across `reset()` and `step()` paths and executed invariant probes for queue/resource/observation coherence.

## Key state mutation paths
1. **Initialization**
   - Scenario builders create observations/hidden state/queue.  
     **Evidence:** `triage_env/app/data/scenario_builder.py:14-32`
   - State registry creates `EnvState` with queue/resources/counters.  
     **Evidence:** `triage_env/app/engine/state/registry.py:11-31`
2. **Step update sequence**
   - Task logic mutates observations/queue/resources.  
     **Evidence:** `triage_env/app/tasks/task_1/scenario.py:52-71`, `triage_env/app/tasks/task_2/scenario.py:61-97`, `triage_env/app/tasks/task_3/scenario.py:68-113`
   - Termination/degradation/resource release engines mutate hidden/env state.  
     **Evidence:** `triage_env/app/engine/termination.py:30-43`, `triage_env/app/engine/resources/release_engine.py:14-38`
   - Registry increments step and recomputes queue ordering.  
     **Evidence:** `triage_env/app/engine/state/registry.py:41-48`

## Integrity checks

### PASS — no ghost patient IDs in queue/resources
- Queue IDs are derived from `patient_hidden_states` keys and maintained through queue operations.  
  **Evidence:** `triage_env/app/data/scenario_builder.py:24-27`, `triage_env/app/engine/queue/sorter.py:26-35`
- Runtime probes did not detect unknown IDs referenced by queue/resource maps.

### PASS — duplicate queue IDs not observed
- Reorder logic removes then inserts a single patient ID.  
  **Evidence:** `triage_env/app/engine/queue/sorter.py:33-35`
- Runtime probes found no duplicate queue IDs.

### FAIL — stale `assigned_resource` in patient observation after discharge/release
- Assignment sets `PatientObservation.assigned_resource`.  
  **Evidence:** `triage_env/app/tasks/task_3/scenario.py:75-78`
- Discharge/release clears `EnvState.resource_occupancy` but does not clear `PatientObservation.assigned_resource`.  
  **Evidence:** `triage_env/app/engine/resources/release_engine.py:6-12`, `triage_env/app/engine/resources/release_engine.py:40-50`
- Runtime probe result: after discharge/auto-release, occupancy is empty while patient observation still shows prior resource.

### FAIL — direct hidden-state mutation without immutable boundary
- `history_unlocked` and deterioration flags mutate in-place.  
  **Evidence:** `triage_env/app/engine/info/history_unlocker.py:13-17`, `triage_env/app/engine/termination.py:37-42`
- This is allowed behaviorally, but no immutable snapshot guarantees are present.

## Desynchronization risk assessment
1. **Observation ↔ resource occupancy mismatch:** confirmed for `assigned_resource` post-release.
2. **Queue ↔ hidden-state mismatch:** not observed in probes; guarded by validator and queue operations.

## Recommendations
1. Clear `assigned_resource` in `patient_observations` when `_free_resource()` or `execute_early_discharge()` succeeds.
2. Add invariant tests that assert observation/resource coherence after every step.

## Phase 3 verdict
**FAIL (state coherence issue)** due stale assigned-resource field after discharge/release.
