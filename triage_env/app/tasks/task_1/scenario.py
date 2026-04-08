# triage_env/app/tasks/task_1/scenario.py
from app.core.models.action import TriageAction, ActionType
from app.core.models.environment import EnvState, StepResult, Reward
from app.core.models.observation import TriageObservation
from app.core.constants.protocols import TASK_1_SCORING_VALUES
from app.data.scenario_builder import build_task_1_scenario
from app.engine.reward_engine import RewardEngine
from app.graders.task_1_grader import grade_task_1
from app.engine.info.history_unlocker import execute_request_info, apply_history_to_observation
from app.tasks.base_task import BaseScenario

class Task1Scenario(BaseScenario):
    """Single patient classification task focusing on ESI baseline accuracy."""

    def __init__(self):
        super().__init__()
        self.reward_engine = RewardEngine()

    def initialize(self) -> tuple[TriageObservation, EnvState]:
        """Set up episode, return first observation and initial state."""
        obs_dict, hid_dict, initial_queue = build_task_1_scenario()
        
        self.patient_observations = obs_dict
        self.patient_hidden_states = hid_dict
        self.env_state = self.state_registry.initialize("task_1", self.patient_observations, self.patient_hidden_states, initial_queue)
        
        return self._build_current_observation(), self.env_state

    def step(self, action: TriageAction) -> StepResult:
        """Process one agent action sequentially through validation and engines."""
        # 1. Check if already done
        if self.env_state.episode_done:
            return StepResult(observation=self._build_current_observation(), reward=Reward(value=0.0), done=True, info={})

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
            # 4. Process CLASSIFY
            if action.action_type == ActionType.CLASSIFY:
                agent_esi = int(action.value)
                true_esi = self.patient_hidden_states[action.patient_id].true_esi_level
                reward = TASK_1_SCORING_VALUES.get(abs(agent_esi - true_esi), 0.0)
                
                if agent_esi == true_esi:
                    self.env_state.stats.correct_classifications += 1
                else:
                    self.env_state.stats.incorrect_classifications += 1
                
                self.env_state.episode_done = True
                
            # 5. Process REQUEST_INFO
            elif action.action_type == ActionType.REQUEST_INFO:
                success, msg, history = execute_request_info(action.patient_id, self.env_state)
                if success:
                    self.patient_observations = apply_history_to_observation(action.patient_id, history, self.patient_observations)
                    self.env_state.stats.request_info_uses += 1
                    reward = -0.1

        # 6. Check termination
        if not self.env_state.episode_done:
            done, term_reason = self.termination_engine.check_termination(self.env_state, self.patient_hidden_states, self.patient_observations)
            if done:
                self.env_state.episode_done = True
                self.env_state.termination_reason = term_reason

        # 6.5 Aggregated reward calculation
        reward, breakdown = self.reward_engine.compute_step_reward(
            action_reward=reward,
            env_state=self.env_state,
            deteriorated_this_step=[],
            critical_patient_assigned=False
        )
        self.env_state.stats.total_reward += reward

        # 7. Update state after step
        self.env_state = self.state_registry.update_after_step(self.env_state, self.patient_observations, self.patient_hidden_states, [])
        
        # 8. Build and return StepResult
        step_info["reward_breakdown"] = breakdown
        return StepResult(observation=self._build_current_observation(), reward=Reward(value=reward), done=self.env_state.episode_done, info=step_info)

    def get_final_score(self) -> tuple[float, dict]:
        """Return normalized episode score 0.0-1.0 based on classification accuracy."""
        return grade_task_1(self.env_state)

    def get_state(self) -> dict:
        """Return full teacher view payload."""
        return self.state_registry.get_teacher_view(self.env_state)
