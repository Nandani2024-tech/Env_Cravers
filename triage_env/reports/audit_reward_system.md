# Phase 5 — Reward Function Audit

## Method
Reviewed reward code paths and executed adversarial policies (`random`, `loop`, `noop`, `spam_invalid`, `reward_hacker`, `heuristic`) across all tasks.

## Reward mechanics (code-level)
1. Step rewards are action-specific plus modifiers.
   - Task 1 classification reward from ESI distance table.  
     **Evidence:** `triage_env/app/tasks/task_1/scenario.py:54-57`, `triage_env/app/core/constants/protocols.py:45-51`
   - Task 2 includes classify/reorder/request-info/discharge rewards.  
     **Evidence:** `triage_env/app/tasks/task_2/scenario.py:61-97`
   - Task 3 includes assign/reorder/request-info/discharge rewards.  
     **Evidence:** `triage_env/app/tasks/task_3/scenario.py:68-113`
2. Global modifiers:
   - Deterioration penalty `-0.5` each
   - Critical assignment bonus `+0.1`
   - Clamp to `[-1.0, 1.0]`  
   **Evidence:** `triage_env/app/engine/reward_engine.py:19-30`

## Range compliance
- **FAIL** against strict `[0.0, 1.0]` criterion: environment intentionally emits negative rewards.  
  **Evidence:** penalties in `triage_env/app/tasks/task_1/scenario.py:49`, `triage_env/app/tasks/task_2/scenario.py:57`, `triage_env/app/tasks/task_3/scenario.py:64-65` and clamp in `triage_env/app/engine/reward_engine.py:30`.
- **PASS** for declared environment range `[-1.0, 1.0]` in metadata.  
  **Evidence:** `triage_env/openenv.yaml:37`

## Adversarial behavior results (runtime)
From probe runs:
- Task 1 loop/no-op: total reward `-6.1`, done=True at max-step path.
- Task 2 loop/no-op: total reward `-1.8`, terminated by critical wait timeout.
- Task 3 loop/no-op: total reward `-2.1`, terminated by critical wait timeout.
- `spam_invalid` policies remain negative across tasks.
- `heuristic` outperforms `random` in total reward across tasks in sampled runs.

## Exploitability assessment
### PASS — obvious farming loops are penalized
- Repeated `request_info` becomes invalid and is penalized.  
  **Evidence:** `triage_env/app/core/validator.py:98-101`
- Wrong-task action spam is penalized by task-id mismatch.  
  **Evidence:** `triage_env/app/core/validator.py:13-15`

### WARNING — “reward_hacker” still attains moderate final score in Task 3
- Discharge of ESI 4/5 gives positive `+0.05`.  
  **Evidence:** `triage_env/app/tasks/task_3/scenario.py:109-113`
- Combined grader weighting can still produce mid score under weak safety/resource behavior.  
  **Evidence:** `triage_env/app/graders/task_3/safety_scorer.py:18-22`, `triage_env/app/graders/task_3/resource_scorer.py:6-11`

## Partial progress signals
- Dense per-step rewards exist for classify/reorder/assign and penalties for invalid/unsafe behavior.  
  **Evidence:** task scenario files above + `triage_env/app/engine/reward_engine.py:19-36`

## Recommendations
1. If validator requires non-negative step rewards, remap rewards before emission or update spec expectation.
2. Tighten Task 3 discharge incentives to reduce “safe-score-with-limited-care” behavior.

## Phase 5 verdict
**PARTIAL FAIL** under strict `0..1` step-reward requirement; **PASS** under declared `-1..1` environment contract.
