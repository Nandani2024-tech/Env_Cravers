# triage_env/app/environment.py
from typing import Optional
from app.core.models.action import TriageAction
from app.core.models.observation import TriageObservation
from app.core.models.environment import EnvState, StepResult
from app.tasks.base_task import BaseScenario
from app.tasks.task_1.scenario import Task1Scenario
from app.tasks.task_2.scenario import Task2Scenario
from app.tasks.task_3.scenario import Task3Scenario

class TriageEnvironment:
    """The central OpenEnv wrapper acting as the primary entry point for all simulation tasks."""

    def __init__(self):
        self.current_scenario: Optional[BaseScenario] = None
        self.current_task_id: Optional[str] = None
        self._scenario_map = {
            "task_1": Task1Scenario,
            "task_2": Task2Scenario,
            "task_3": Task3Scenario
        }

    def reset(self, task_id: str) -> TriageObservation:
        """Instantiates and initializes a fresh scenario for the specified task ID."""
        if task_id not in self._scenario_map:
            raise ValueError(f"Unsupported task_id: {task_id}. Valid: {list(self._scenario_map.keys())}")
            
        self.current_task_id = task_id
        self.current_scenario = self._scenario_map[task_id]()
        obs, _ = self.current_scenario.initialize()
        return obs

    def step(self, action: TriageAction) -> StepResult:
        """Processes an agent action through the active scenario's simulation loop."""
        if self.current_scenario is None:
            raise RuntimeError("Call reset() before step()")
        return self.current_scenario.step(action)

    def state(self) -> dict:
        """Returns the full internal teacher view of the current environment state."""
        if self.current_scenario is None:
            return {"error": "Environment not initialized. Call reset() first."}
        return self.current_scenario.get_state()

    def get_final_score(self) -> float:
        """Computes the final performance score for the current episode."""
        if self.current_scenario is None:
            return 0.0
        return self.current_scenario.get_final_score()

# Single shared instance for access by API routes
environment = TriageEnvironment()
