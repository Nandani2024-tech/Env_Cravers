# triage_env/app/engine/state/registry.py
from app.core.constants.resources import ALL_RESOURCE_IDS, BED_TYPES, DOCTOR_IDS, TRAUMA_BAY_IDS, DISCHARGE_AREA_ID
from app.core.models.environment import EnvState, EpisodeStats, PatientHiddenState
from app.core.models.observation import TriageObservation, PatientObservation, ResourceObservation
from app.engine.queue.sorter import calculate_optimal_queue
from app.engine.state.base import BaseStateTracker

class StateRegistry(BaseStateTracker):
    """Concrete implementation mapping state management to atomic engines."""
    
    def initialize(
        self,
        task_id: str,
        patient_observations: dict[str, PatientObservation],
        patient_hidden_states: dict[str, PatientHiddenState],
        initial_queue: list[str]
    ) -> EnvState:
        """Instantiates EnvState, zeroes counters, and calculates starting bounds."""
        optimal_queue = calculate_optimal_queue(patient_hidden_states, patient_observations, initial_queue)
        
        resource_occupancy = {rid: None for rid in ALL_RESOURCE_IDS}
        resource_release_countdowns = {rid: None for rid in ALL_RESOURCE_IDS}
        
        return EnvState(
            task_id=task_id,
            patient_hidden_states=patient_hidden_states,
            optimal_queue_order=optimal_queue,
            resource_occupancy=resource_occupancy,
            resource_release_countdowns=resource_release_countdowns,
            stats=EpisodeStats()
        )

    def update_after_step(
        self,
        env_state: EnvState,
        patient_observations: dict[str, PatientObservation],
        patient_hidden_states: dict[str, PatientHiddenState],
        discharged_this_step: list[str]
    ) -> EnvState:
        """Updates clocks and syncs dynamic datasets after atomic engines finish their operations."""
        env_state.current_step += 1
        env_state.stats.total_steps = env_state.current_step
        
        env_state.optimal_queue_order = calculate_optimal_queue(
            patient_hidden_states,
            patient_observations,
            env_state.optimal_queue_order
        )
        
        for pid in discharged_this_step:
            if pid in env_state.optimal_queue_order:
                env_state.optimal_queue_order.remove(pid)
                
        return env_state

    def get_teacher_view(self, env_state: EnvState) -> dict:
        """Extracts deep state dictionary for observation by evaluators or logging layer."""
        return env_state.model_dump()

    def build_observation(
        self,
        env_state: EnvState,
        patient_observations: dict[str, PatientObservation],
        task_id: str
    ) -> TriageObservation:
        """Bakes the internal state into the formal schema required by the OpenEnv interface."""
        resources_list = []
        for rid in ALL_RESOURCE_IDS:
            r_type = "Unknown"
            if rid in BED_TYPES:
                r_type = BED_TYPES[rid]
            elif rid in DOCTOR_IDS:
                r_type = "Doctor"
            elif rid in TRAUMA_BAY_IDS:
                r_type = "Trauma"
            elif rid == DISCHARGE_AREA_ID:
                r_type = "Discharge"
                
            obs = ResourceObservation(
                resource_id=rid,
                resource_type=r_type,
                is_occupied=(env_state.resource_occupancy.get(rid) is not None),
                occupied_by=env_state.resource_occupancy.get(rid),
                steps_until_free=env_state.resource_release_countdowns.get(rid)
            )
            resources_list.append(obs)
            
        return TriageObservation(
            task_id=task_id,
            current_step=env_state.current_step,
            elapsed_minutes=env_state.current_step * 5,
            patients=list(patient_observations.values()),
            resources=resources_list,
            queue_order=env_state.optimal_queue_order,
            episode_done=env_state.episode_done,
            info={}
        )
