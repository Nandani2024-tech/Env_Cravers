# Phase 7 — RL Environment Design Quality

## Method
Evaluated observation/action/reward/transition design against RL learnability criteria and checked whether incentives align with intended policy quality.

## Observation space quality
- Rich patient-level features: vitals, symptoms, waiting time, change flags, optional history.  
  **Evidence:** `triage_env/app/core/models/observation.py:22-37`
- Resource-level features include occupancy and release countdown.  
  **Evidence:** `triage_env/app/core/models/observation.py:38-45`
- Global episode context includes queue, step, elapsed time, done.  
  **Evidence:** `triage_env/app/core/models/observation.py:46-55`

## Action space quality
- Clearly constrained discrete action types and typed payloads.  
  **Evidence:** `triage_env/app/core/models/action.py:7-13`, `triage_env/app/core/models/action.py:26-47`
- Task-scoped legality enforced by validator.  
  **Evidence:** `triage_env/app/core/validator.py:13-25`, `triage_env/app/core/validator.py:28-115`

## Transition dynamics
- Dynamic deterioration and resource release introduce non-trivial temporal dynamics.  
  **Evidence:** `triage_env/app/engine/vitals/calculator.py:43-63`, `triage_env/app/engine/termination.py:30-43`, `triage_env/app/engine/resources/release_engine.py:14-38`
- Queue ordering updates every step by hidden ESI + wait-time.  
  **Evidence:** `triage_env/app/engine/state/registry.py:44-48`, `triage_env/app/engine/queue/sorter.py:12-18`

## Reward density and alignment
- Dense shaping exists at step level (classify/reorder/assign/info/discharge + modifiers).  
  **Evidence:** `triage_env/app/tasks/task_1/scenario.py:53-71`, `triage_env/app/tasks/task_2/scenario.py:61-97`, `triage_env/app/tasks/task_3/scenario.py:68-113`, `triage_env/app/engine/reward_engine.py:19-36`
- Final graders are normalized to `[0,1]` and include safety dimensions.  
  **Evidence:** task grader files cited in Phase 6 report.

## RL learnability assessment
### Strengths
1. Sparse-to-dense mix supports credit assignment.
2. Safety penalties make degenerate loops unattractive.
3. Task difficulty progression (`task_1` → `task_3`) is structurally present.  
   **Evidence:** `triage_env/openenv.yaml:15-30`

### Weaknesses
1. **Strong determinism across resets** may encourage memorization over generalization.  
   **Evidence:** `triage_env/app/core/seeds.py:29-31`, `triage_env/app/data/scenario_builder.py:36-47`
2. **Task 2 grader shortcut** can reward agents without true reprioritization skill.  
   **Evidence:** `triage_env/app/engine/queue/sorter.py:49-50`, `triage_env/app/tasks/task_2/scenario.py:69-75`
3. **State staleness after discharge/release** reduces observation trustworthiness.  
   **Evidence:** set on assign `triage_env/app/tasks/task_3/scenario.py:75-78`; no clear on release/discharge `triage_env/app/engine/resources/release_engine.py:6-12`, `40-50`

## Can agents actually learn?
- **YES**, but with caveats. Heuristic policy outperformed random/no-op in probes.
- Generalization quality is likely limited by deterministic scenario generation.

## Phase 7 verdict
**PARTIAL PASS** — RL structure is meaningful, but determinism + Task 2 grading shortcut + stale observation field weaken production-grade learning quality.
