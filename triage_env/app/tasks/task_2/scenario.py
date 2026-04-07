# triage_env/app/tasks/task_2/scenario.py
import random
from app.core.models.action import TriageAction, ActionType
from app.core.models.environment import EnvState, StepResult
from app.core.models.observation import TriageObservation
from app.core.constants.protocols import TASK_1_SCORING_VALUES
from app.data.scenario_builder import build_task_2_scenario
from app.engine.queue.sorter import execute_reorder, get_queue_score, increment_wait_steps, calculate_optimal_queue
from app.engine.info.history_unlocker import execute_request_info, apply_history_to_observation
from app.engine.resources.release_engine import process_step_releases, execute_early_discharge
from app.engine.vitals.calculator import calculate_next_vitals
from app.engine.vitals.status_manager import get_status_update
from app.engine.reward_engine import RewardEngine
from app.graders.task_2_grader import grade_task_2
from app.tasks.base_task import BaseScenario

class Task2Scenario(BaseScenario):
    """Dynamic queue reprioritization task with 10 patients."""
    
    def __init__(self):
        super().__init__()
        self.deterioration_step: int = 5
        self.classified_patients: set[str] = set()
        self.reward_engine = RewardEngine()

    def initialize(self) -> tuple[TriageObservation, EnvState]:
        """Set up episode, return first observation and initial state."""
        self.classified_patients = set()
        obs_dict, hid_dict, initial_queue = build_task_2_scenario()
        
        self.patient_observations = obs_dict
        self.patient_hidden_states = hid_dict
        self.env_state = self.state_registry.initialize("task_2", self.patient_observations, self.patient_hidden_states, initial_queue)
        
        return self._build_current_observation(), self.env_state

    def step(self, action: TriageAction) -> StepResult:
        """Process one agent action and manage dynamic queue deterioration."""
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
            # 4. Process action based on type
            if action.action_type == ActionType.CLASSIFY:
                agent_esi = int(action.value)
                true_esi = self.patient_hidden_states[action.patient_id].true_esi_level
                reward = TASK_1_SCORING_VALUES.get(abs(agent_esi - true_esi), 0.0)
                if agent_esi == true_esi:
                    self.env_state.stats.correct_classifications += 1
                else:
                    self.env_state.stats.incorrect_classifications += 1
                self.classified_patients.add(action.patient_id)
                
            elif action.action_type == ActionType.REORDER:
                current_opt_queue = calculate_optimal_queue(self.patient_hidden_states, self.patient_observations, self.env_state.optimal_queue_order)
                current_score = get_queue_score(self.env_state.optimal_queue_order, current_opt_queue)
                
                execute_reorder(action.patient_id, int(action.value), self.env_state)
                
                new_score = get_queue_score(self.env_state.optimal_queue_order, current_opt_queue)
                reward = 0.1 if new_score > current_score else -0.05
                
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

        # 5. Dynamic update on deterioration step
        if self.env_state.current_step == self.deterioration_step:
            unassigned = [p for p in self.env_state.optimal_queue_order]
            targets = random.sample(unassigned, min(2, len(unassigned)))
            for pid in targets:
                old_obs = self.patient_observations[pid]
                # Simulate patient deterioration (is_treated=False, double jump)
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
        reward = self.reward_engine.compute_step_reward(
            action_reward=reward,
            env_state=self.env_state,
            deteriorated_this_step=deteriorated_this_step,
            critical_patient_assigned=False
        )
        self.env_state.stats.total_reward += reward

        # 9. Check termination
        if not self.env_state.optimal_queue_order and len(self.classified_patients) == len(self.patient_observations):
            self.env_state.episode_done = True
        else:
            done, term_reason = self.termination_engine.check_termination(self.env_state, self.patient_hidden_states, self.patient_observations)
            if done:
                self.env_state.episode_done = True
                self.env_state.termination_reason = term_reason

        # 10. Update state
        self.env_state = self.state_registry.update_after_step(self.env_state, self.patient_observations, self.patient_hidden_states, discharged)
        
        # 11. Return StepResult
        return StepResult(observation=self._build_current_observation(), reward=reward, done=self.env_state.episode_done, info=step_info)

    def get_final_score(self) -> float:
        """Return combined normalized score for classifications and queue ordering."""
        return grade_task_2(self.env_state, self.patient_hidden_states, self.patient_observations, self.env_state.optimal_queue_order)

    def get_state(self) -> dict:
        """Return full teacher view payload."""
        return self.state_registry.get_teacher_view(self.env_state)
