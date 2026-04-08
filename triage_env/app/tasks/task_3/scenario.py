# triage_env/app/tasks/task_3/scenario.py
import random
from app.core.models.action import TriageAction, ActionType
from app.core.models.environment import EnvState, StepResult
from app.core.models.observation import TriageObservation
from app.data.scenario_builder import build_task_3_scenario
from app.engine.queue.sorter import execute_reorder, increment_wait_steps, get_queue_score, calculate_optimal_queue
from app.engine.info.history_unlocker import execute_request_info, apply_history_to_observation
from app.engine.resources.allocator import execute_assignment
from app.engine.resources.release_engine import process_step_releases, execute_early_discharge
from app.engine.vitals.calculator import calculate_next_vitals
from app.engine.vitals.status_manager import get_status_update
from app.engine.reward_engine import RewardEngine
from app.graders.task_3.resource_scorer import score_resource_assignments
from app.graders.task_3.time_scorer import score_wait_times
from app.graders.task_3.safety_scorer import score_safety, get_task_3_final_score
from app.tasks.base_task import BaseScenario

class Task3Scenario(BaseScenario):
    """Full ER management task with 15 patients and resource allocation."""
    
    def __init__(self):
        super().__init__()
        self.deterioration_steps: list[int] = [5, 10, 15]
        self.assigned_patients: set[str] = set()
        self.assigned_correctly: int = 0
        self.assigned_incorrectly: int = 0
        self.reward_engine = RewardEngine()

    def initialize(self) -> tuple[TriageObservation, EnvState]:
        """Set up episode, return first observation and initial state."""
        self.assigned_patients = set()
        self.assigned_correctly = 0
        self.assigned_incorrectly = 0
        
        obs_dict, hid_dict, initial_queue = build_task_3_scenario()
        self.patient_observations = obs_dict
        self.patient_hidden_states = hid_dict
        self.env_state = self.state_registry.initialize("task_3", self.patient_observations, self.patient_hidden_states, initial_queue)
        
        return self._build_current_observation(), self.env_state

    def step(self, action: TriageAction) -> StepResult:
        """Process one agent action iteratively managing ER state."""
        # 1. Check if already done
        if self.env_state.episode_done:
            return StepResult(observation=self._build_current_observation(), reward=0.0, done=True, info={})

        # 2. Validate action
        is_valid, reason = self.validator.validate(action, self.env_state, self.patient_observations)
        
        reward = 0.0
        step_info = {}
        
        # 3. Handle invalid action
        if not is_valid:
            self.env_state.stats.invalid_actions += 1
            reward = -0.2
            step_info = {"error": reason}
        else:
            # 4. Process action
            if action.action_type == ActionType.ASSIGN:
                esi = self.patient_hidden_states[action.patient_id].true_esi_level
                success, msg = execute_assignment(action.patient_id, str(action.value), esi, self.env_state)
                if success:
                    self.assigned_patients.add(action.patient_id)
                    opt_res = self.patient_hidden_states[action.patient_id].optimal_resource
                    
                    if action.value == opt_res:
                        self.assigned_correctly += 1
                        reward = 0.8
                    else:
                        self.assigned_incorrectly += 1
                        reward = 0.4
                else:
                    reward = -0.2
                    
            elif action.action_type == ActionType.REORDER:
                current_opt = calculate_optimal_queue(self.patient_hidden_states, self.patient_observations, self.env_state.optimal_queue_order)
                c_score = get_queue_score(self.env_state.optimal_queue_order, current_opt)
                
                execute_reorder(action.patient_id, int(action.value), self.env_state)
                
                n_score = get_queue_score(self.env_state.optimal_queue_order, current_opt)
                reward = 0.1 if n_score > c_score else -0.05
                
            elif action.action_type == ActionType.REQUEST_INFO:
                success, msg, hist = execute_request_info(action.patient_id, self.env_state)
                if success:
                    self.patient_observations = apply_history_to_observation(action.patient_id, hist, self.patient_observations)
                    self.env_state.stats.request_info_uses += 1
                    reward = -0.1
                    
            elif action.action_type == ActionType.DISCHARGE:
                success, msg = execute_early_discharge(action.patient_id, self.env_state)
                if success:
                    esi = self.patient_hidden_states[action.patient_id].true_esi_level
                    reward = 0.05 if esi in [4, 5] else -0.3

        # 5. Dynamic update on deterioration steps
        if self.env_state.current_step in self.deterioration_steps:
            unassigned = [p for p in self.env_state.optimal_queue_order]
            targets = random.sample(unassigned, min(3, len(unassigned)))
            for pid in targets:
                old_obs = self.patient_observations[pid]
                new_vitals = calculate_next_vitals(old_obs.vitals, self.patient_hidden_states[pid].true_esi_level, is_treated=False)
                new_vitals = calculate_next_vitals(new_vitals, self.patient_hidden_states[pid].true_esi_level, is_treated=False)
                self.patient_observations[pid] = get_status_update(old_obs.vitals, new_vitals, old_obs)

        # 6. Increment wait_steps
        self.patient_observations = increment_wait_steps(self.env_state, self.patient_observations)
        
        # 7. Decrement deterioration counters
        deteriorated_this_step = self.termination_engine.decrement_deterioration_counters(self.env_state)
        
        # 8. Process auto-releases
        discharged = process_step_releases(self.env_state)

        # 8.5 Aggregated reward calculation
        critical_assigned = False
        if action.action_type == ActionType.ASSIGN and self.patient_hidden_states[action.patient_id].true_esi_level <= 2:
            critical_assigned = True

        reward, breakdown = self.reward_engine.compute_step_reward(
            action_reward=reward,
            env_state=self.env_state,
            deteriorated_this_step=deteriorated_this_step,
            critical_patient_assigned=critical_assigned
        )
        self.env_state.stats.total_reward += reward

        # 9. Check termination
        if not self.env_state.optimal_queue_order and len(self.assigned_patients) == len(self.patient_observations):
            self.env_state.episode_done = True
        else:
            done, term_reason = self.termination_engine.check_termination(self.env_state, self.patient_hidden_states, self.patient_observations)
            if done:
                self.env_state.episode_done = True
                self.env_state.termination_reason = term_reason

        # 10. Update state
        self.env_state = self.state_registry.update_after_step(self.env_state, self.patient_observations, self.patient_hidden_states, discharged)
        
        # 11. Return StepResult
        step_info["reward_breakdown"] = breakdown
        return StepResult(observation=self._build_current_observation(), reward=reward, done=self.env_state.episode_done, info=step_info)

    def get_final_score(self) -> tuple[float, dict]:
        """Return the complex weighted score for resource allocation (Task 3)."""
        res_score = score_resource_assignments(self.assigned_correctly, self.assigned_incorrectly, len(self.patient_observations))
        time_score = score_wait_times(self.patient_hidden_states, self.patient_observations)
        safety_score = score_safety(self.env_state, len(self.patient_observations))
        
        return get_task_3_final_score(res_score, time_score, safety_score)

    def get_state(self) -> dict:
        """Return full teacher view payload."""
        return self.state_registry.get_teacher_view(self.env_state)
