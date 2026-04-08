# Phase 4 — Episode Lifecycle Safety Audit

## Method
Analyzed `done` transitions and termination conditions in code and ran loop policies to validate liveness/safety.

## Start conditions
- Episodes only start after `reset()` creates a scenario.  
  **Evidence:** `triage_env/app/environment.py:31-34`
- Calling `step()` without reset raises runtime error.  
  **Evidence:** `triage_env/app/environment.py:38-40`

## Done/termination logic by component
1. **Task-local completion**
   - Task 1 ends on first `CLASSIFY`.  
     **Evidence:** `triage_env/app/tasks/task_1/scenario.py:53-64`
   - Task 2 ends when queue empty and all patients classified.  
     **Evidence:** `triage_env/app/tasks/task_2/scenario.py:129-130`
   - Task 3 ends when queue empty and all patients assigned at least once.  
     **Evidence:** `triage_env/app/tasks/task_3/scenario.py:144-145`
2. **Global termination**
   - Max-step cutoff and critical-wait timeout.  
     **Evidence:** `triage_env/app/engine/termination.py:18-27`, `triage_env/app/engine/termination.py:45-49`, `triage_env/app/engine/termination.py:65-67`

## Safety findings

### PASS — dead loops are bounded
- Loop/no-op policies terminate via max-step or critical timeout in all tasks.

### FAIL — max-step off-by-one behavior
- Termination checks happen before `current_step` increment.  
  **Evidence:** termination check in tasks: `triage_env/app/tasks/task_1/scenario.py:74-78`, `triage_env/app/tasks/task_2/scenario.py:132-135`, `triage_env/app/tasks/task_3/scenario.py:147-150`
- Step counter increments in `update_after_step()` afterward.  
  **Evidence:** `triage_env/app/engine/state/registry.py:41-43`
- Result: episodes can execute 31 actions when `MAX_STEPS=30` (observed in runtime probe).

### PASS — post-done stepping is safe
- Each task returns `done=True` with zero reward for further calls after completion.  
  **Evidence:** `triage_env/app/tasks/task_1/scenario.py:32-38`, `triage_env/app/tasks/task_2/scenario.py:40-46`, `triage_env/app/tasks/task_3/scenario.py:46-52`

## Infinite-loop risk
- No unbounded loop found in environment internals.  
- Runtime loop/spam/no-op probes always terminated.

## Recommendations
1. Move max-step check to post-increment boundary or compare against `current_step + 1`.
2. Add explicit lifecycle test asserting `steps_taken <= MAX_STEPS`.

## Phase 4 verdict
**PARTIAL FAIL** — lifecycle is safe from infinite loops, but max-step boundary is off by one.
