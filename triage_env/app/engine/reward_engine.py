# triage_env/app/engine/reward_engine.py
from app.core.models.environment import EnvState

class RewardEngine:
    """Aggregates action-level rewards and applies global simulation modifiers."""

    def compute_step_reward(
        self,
        action_reward: float,
        env_state: EnvState,
        deteriorated_this_step: list[str],
        critical_patient_assigned: bool = False
    ) -> float:
        """Computes the final step reward by applying clinical safety and speed modifiers."""
        reward = action_reward

        # Modifier 1: Heavy penalty for preventable clinical deterioration (-0.5 per patient)
        if deteriorated_this_step:
            reward -= (len(deteriorated_this_step) * 0.5)

        # Modifier 2: Time pressure bonus (+0.1) for assigning ESI 1-2 patients quickly
        if critical_patient_assigned:
            reward += 0.1

        # Final reward is clamped to the standard range [-1.0, 1.0]
        return max(-1.0, min(1.0, reward))
