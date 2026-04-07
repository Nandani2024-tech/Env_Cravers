import os
import sys

# Add root project dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
from app.core.config import settings

def invalid_action():
    # REORDER is not allowed in task_1, making it an invalid action always.
    return TriageAction(action_type=ActionType.REORDER, patient_id="p1", task_id="task_1", value="1")

def valid_action(obs):
    # Use REQUEST_INFO since CLASSIFY immediately concludes the episode in task_1
    if not hasattr(valid_action, 'requested'):
        valid_action.requested = set()
    
    for p in obs.patients:
        if p.patient_id not in valid_action.requested:
            valid_action.requested.add(p.patient_id)
            return TriageAction(action_type=ActionType.REQUEST_INFO, patient_id=p.patient_id, task_id="task_1", value="")
    
    return invalid_action()


def run_test_1():
    print("--- TEST 1 — INVALID ACTION SPAM ---")
    obs = environment.reset("task_1")
    for i in range(10):
        action = invalid_action()
        res = environment.step(action)
        print(f"Step: {environment.current_scenario.env_state.current_step}")

def run_test_2():
    print("--- TEST 2 — MAX STEP TERMINATION ---")
    obs = environment.reset("task_1")
    steps = 0
    done = False
    while not done:
        action = invalid_action()
        res = environment.step(action)
        done = res.done
        steps += 1
        print(f"step: {environment.current_scenario.env_state.current_step}")
        if steps > 40:
            print("Infinite loop detected!")
            break
    print(f"done = {done}")

def run_test_3():
    print("--- TEST 3 — MIXED VALID + INVALID ACTIONS ---")
    obs = environment.reset("task_1")
    valid_action.requested = set()
    actions = [
        valid_action(obs),
        invalid_action(),
        invalid_action(),
        valid_action(obs),
        invalid_action()
    ]
    for action in actions:
        is_invalid = action.action_type == ActionType.REORDER
        res = environment.step(action)
        prefix = "invalid" if is_invalid else "valid"
        print(f"step {environment.current_scenario.env_state.current_step} {prefix} | reward: {res.reward} done: {res.done}")

def run_test_4():
    print("--- TEST 4 — TERMINATION AFTER INVALID ACTION ---")
    obs = environment.reset("task_1")
    # Force max steps
    environment.current_scenario.env_state.current_step = settings.MAX_STEPS - 1
    action = invalid_action()
    res = environment.step(action)
    print(f"Step: {environment.current_scenario.env_state.current_step}")
    print(f"Reward: {res.reward}")
    print(f"Done: {res.done}")
    reason = environment.current_scenario.env_state.termination_reason
    print(f"termination_reason: '{reason}'")

def run_test_5():
    print("--- TEST 5 — REWARD ENGINE STABILITY ---")
    obs = environment.reset("task_1")
    for i in range(5):
        action = invalid_action()
        res = environment.step(action)
        print(f"Step {environment.current_scenario.env_state.current_step} reward: {res.reward} total: {environment.current_scenario.env_state.stats.total_reward}")

if __name__ == "__main__":
    run_test_1()
    print("")
    run_test_2()
    print("")
    run_test_3()
    print("")
    run_test_4()
    print("")
    run_test_5()
