# triage_env/app/api/routes.py
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.models.action import TriageAction
from app.core.models.observation import TriageObservation
from app.core.models.environment import StepResult
from app.environment import environment

class ResetRequest(BaseModel):
    """Container for the task_id parameter during environment reset operations."""
    task_id: Optional[str] = None

router = APIRouter()

@router.post("/reset", response_model=TriageObservation)
async def reset(request: Optional[ResetRequest] = None):
    """Instantiates a fresh episode scenario and returns the starting state."""
    try:
        obs = environment.reset(request.task_id if request else None)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/step", response_model=StepResult)
async def step(action: TriageAction):
    """Processes an agent action and returns the resulting simulation state and reward."""
    try:
        result = environment.step(action)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error during step execution.")

@router.get("/state")
async def state():
    """Returns the internal high-fidelity state representation (Teacher View)."""
    return environment.state()

@router.get("/health")
async def health():
    """Confirms availability and versions of the environment service."""
    return {"status": "ok", "environment": "clinical-triage", "version": "1.0.0"}

@router.get("/score")
async def score():
    """Retrieves the performance metrics for the current active episode."""
    result = environment.get_final_score()
    return {
        "score": result["score"],
        "details": result.get("details", {}),
        "task_id": environment.current_task_id
    }
