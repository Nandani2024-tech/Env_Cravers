# Phase 9 — Hackathon Evaluation Scorecard

Scored against requested dimensions (100 total).

## 1) Real-world utility (30) — **26/30**
- Strong healthcare relevance and clear ER triage framing.  
  **Evidence:** `triage_env/README.md:3-7`, `triage_env/openenv.yaml:3-6`
- Uses recognizable ESI medical structure and constrained resources.  
  **Evidence:** `triage_env/app/core/constants/resources.py:23-54`, `triage_env/app/core/constants/protocols.py:3-10`

## 2) Task & grader quality (25) — **17/25**
- Deterministic, bounded scorers exist for all tasks.  
  **Evidence:** grader files and clamps: `task_1_grader.py:21`, `task_2_grader.py:27`, `safety_scorer.py:22`
- Task progression easy→medium→hard is explicit.  
  **Evidence:** `triage_env/openenv.yaml:16-30`
- Deduction: Task 2 queue-score shortcut can award full queue score when queue is empty.  
  **Evidence:** `triage_env/app/engine/queue/sorter.py:49-50` + `triage_env/app/tasks/task_2/scenario.py:69-75`

## 3) Environment design (20) — **13/20**
- Clear separation of API, environment wrapper, engines, tasks, graders.  
  **Evidence:** module layout and imports, e.g., `triage_env/app/tasks/task_3/scenario.py:6-17`
- Deduction: state coherence issue (`assigned_resource` stale post-release/discharge).  
  **Evidence:** set on assign `task_3/scenario.py:75-78`; release clears only occupancy `release_engine.py:6-12`, `40-50`
- Deduction: max-step off-by-one lifecycle boundary.  
  **Evidence:** `termination.py:47` and `state/registry.py:41-43`

## 4) Code quality & spec compliance (15) — **13/15**
- OpenEnv compatibility models and metadata present.  
  **Evidence:** `environment.py:23-27`, `core/models/environment.py:38-90`, `openenv.yaml:8-14`
- API contracts are typed and structured.  
  **Evidence:** `api/routes.py:16-30`
- Minor deduction for validator/logging ambiguity around serialized Reward shape requirements.  
  **UNKNOWN — insufficient evidence in repository** for official validator expectation of reward wire format.

## 5) Creativity & novelty (10) — **8/10**
- Strong domain novelty for triage operations and safety/resource coupling.  
  **Evidence:** `README.md:5-7`, `task_3/scenario.py:115-140`
- Deduction: deterministic reset design limits scenario diversity.  
  **Evidence:** `core/seeds.py:29-31`, `data/scenario_builder.py:36-47`

## Total score
**77 / 100**

## Interpretation
- This is likely competitive for Round-1 functionality screening.
- Main score drag is not missing plumbing; it is integrity and learning-quality issues (Task 2 grading shortcut, stale observation field, lifecycle boundary bug).
