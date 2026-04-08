# Phase 1 — Repository Architecture Audit

## Scope
Inspected the RL environment repository structure and required OpenEnv submission artifacts.

## Directory map (environment-relevant)
```text
triage_env/
  app/
    api/
    core/
      constants/
      models/
    data/
    engine/
      info/
      queue/
      resources/
      state/
      vitals/
    graders/
      task_3/
    tasks/
      task_1/
      task_2/
      task_3/
    utils/
  scripts/
    launcher.py
    debug_tests/
  tests/
    unit/
    integration/
  openenv.yaml
  Dockerfile
  inference.py
  verify_api.py
  requirements.txt
```

## Required component checks
1. **Environment entrypoint present** — `scripts/launcher.py` launches `app.api.main:app` via uvicorn.  
   **Evidence:** `triage_env/scripts/launcher.py:4-10`
2. **OpenEnv spec file present** — `openenv.yaml` exists with name/tasks/entrypoint/tags.  
   **Evidence:** `triage_env/openenv.yaml:1-42`
3. **Task definitions present in both metadata and code**  
   - Metadata tasks: `task_1`, `task_2`, `task_3`  
     **Evidence:** `triage_env/openenv.yaml:15-30`
   - Runtime mapping to scenarios exists  
     **Evidence:** `triage_env/app/environment.py:17-21`
4. **Grader modules present**  
   - Task 1 grader: `grade_task_1`  
     **Evidence:** `triage_env/app/graders/task_1_grader.py:4-25`
   - Task 2 grader: `grade_task_2`  
     **Evidence:** `triage_env/app/graders/task_2_grader.py:7-28`
   - Task 3 sub-graders + final combiner  
     **Evidence:** `triage_env/app/graders/task_3/resource_scorer.py:4-11`, `triage_env/app/graders/task_3/time_scorer.py:6-23`, `triage_env/app/graders/task_3/safety_scorer.py:18-30`
5. **Inference script present** — baseline client with task loop and logs.  
   **Evidence:** `triage_env/inference.py:15-17`, `triage_env/inference.py:215-267`
6. **Docker deployment present** — `Dockerfile` exposes 8000 and runs launcher.  
   **Evidence:** `triage_env/Dockerfile:13-22`

## Placement and packaging assessment
- **PASS:** Core packages are separated by responsibility (`core`, `engine`, `tasks`, `graders`).  
  **Evidence:** `triage_env/app/` tree + imports in `triage_env/app/tasks/task_3/scenario.py:6-17`
- **PASS:** API layer is isolated from simulation logic.  
  **Evidence:** `triage_env/app/api/routes.py:25-34`, `triage_env/app/environment.py:36-40`
- **PASS:** Scenario-specific logic is isolated by task module.  
  **Evidence:** `triage_env/app/tasks/task_1/scenario.py:12-107`, `triage_env/app/tasks/task_2/scenario.py:17-155`, `triage_env/app/tasks/task_3/scenario.py:19-174`

## Missing / weak components
1. **`scripts/validate.sh` exists but is empty** — no shell-level validation entrypoint documented.  
   **UNKNOWN — insufficient evidence in repository** whether OpenEnv judges require this script.
2. **Repository includes prior ad-hoc audit artifacts (`audit_tests/`, old `reports/`)**.  
   This is not a functional blocker but may cause reviewer noise.

## Hackathon requirement coverage (structural)
- OpenEnv metadata file: **Covered**
- API service entrypoint: **Covered**
- Task/Grader modules: **Covered**
- Baseline inference script: **Covered**
- Docker packaging: **Covered**

## Phase 1 verdict
**PASS with minor hygiene concerns** — architecture is complete and submission-shaped.
