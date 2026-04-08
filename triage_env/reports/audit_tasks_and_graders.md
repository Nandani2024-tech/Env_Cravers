# Phase 6 — Task and Grader Validation

## Method
Reviewed grader formulas and task completion rules; ran repeated trajectory checks and multi-policy episodes.

## Task 1
- **Task logic:** single-patient classify/request_info, done on classify.  
  **Evidence:** `triage_env/app/tasks/task_1/scenario.py:53-64`
- **Grader:** accuracy with invalid-action penalty and optional info bonus.  
  **Evidence:** `triage_env/app/graders/task_1_grader.py:11-22`
- **Determinism:** same trajectory returns same score across runs.
- **Score range:** clamped to `[0,1]` in grader.  
  **Evidence:** `triage_env/app/graders/task_1_grader.py:21`
- **Finding:** deterministic and bounded; no constant-score bug across different policies.

## Task 2
- **Task logic:** classification removes patient from queue (`queue` shrinks to empty when all classified).  
  **Evidence:** `triage_env/app/tasks/task_2/scenario.py:69-75`
- **Grader:** weighted classification + queue + speed - penalties.  
  **Evidence:** `triage_env/app/graders/task_2_grader.py:14-27`
- **Critical fairness concern:** queue score can become trivially `1.0` when final queue is empty.
  - `get_queue_score()` returns `1.0` if queue is empty.  
    **Evidence:** `triage_env/app/engine/queue/sorter.py:49-50`
  - Therefore, an agent can avoid meaningful reprioritization and still receive full queue component by classifying everyone.
- **Determinism:** same trajectory score reproducible.
- **Score range:** clamped `[0,1]`.

## Task 3
- **Task logic:** resource assignment with deterioration/release/discharge paths.  
  **Evidence:** `triage_env/app/tasks/task_3/scenario.py:68-113`, `triage_env/app/engine/resources/release_engine.py:14-50`
- **Graders:** resource precision+coverage + wait-time + safety weighted final score.  
  **Evidence:** `triage_env/app/graders/task_3/resource_scorer.py:6-11`, `triage_env/app/graders/task_3/time_scorer.py:14-23`, `triage_env/app/graders/task_3/safety_scorer.py:18-22`
- **Determinism:** same trajectory score reproducible.
- **Score range:** each component and final score clamped `[0,1]`.

## Reproducibility and variance findings
1. **Deterministic by design:** fixed per-task seeds are applied every reset.  
   **Evidence:** `triage_env/app/core/seeds.py:6-10`, `triage_env/app/core/seeds.py:29-31`, `triage_env/app/data/scenario_builder.py:36-47`
2. **Important side effect:** reset seeding uses global `random.seed`, which can also reset same-process agent randomness.
   - This can collapse policy variance in in-process evaluations.

## PASS/FAIL summary
- Deterministic scoring: **PASS**
- Score range `[0,1]`: **PASS**
- Reproducibility across runs: **PASS**
- No constant scores across trajectories/policies: **PASS**
- Grader fairness: **PARTIAL FAIL** (Task 2 queue-score trivialization when queue empties)

## Phase 6 verdict
**PARTIAL FAIL** due Task 2 queue-grading shortcut; otherwise deterministic and bounded.
