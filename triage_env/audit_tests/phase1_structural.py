#!/usr/bin/env python3
"""
PHASE 1 — STRUCTURAL VALIDATION
Tests core OpenEnv interface compliance and robustness.
"""
import sys
sys.path.insert(0, '/home/vedu/Work/Env_Cravers/triage_env')

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
from typing import List, Dict, Any
import json

class StructuralValidator:
    def __init__(self):
        self.results = []
        self.env = environment
        
    def log(self, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"  → {details}")
    
    def test_reset_returns_observation(self):
        """Test that reset() returns a valid observation."""
        try:
            obs = self.env.reset("task_1")
            assert hasattr(obs, 'task_id'), "Observation missing task_id"
            assert hasattr(obs, 'current_step'), "Observation missing current_step"
            assert hasattr(obs, 'patients'), "Observation missing patients"
            self.log("reset() returns valid observation", True, f"task_id={obs.task_id}, patients={len(obs.patients)}")
            return True
        except Exception as e:
            self.log("reset() returns valid observation", False, str(e))
            return False
    
    def test_step_returns_stepresult(self):
        """Test that step() returns observation, reward, done, info."""
        try:
            self.env.reset("task_1")
            action = TriageAction(
                task_id="task_1",
                action_type=ActionType.REQUEST_INFO,
                patient_id="P001",
                value=None
            )
            result = self.env.step(action)
            
            assert hasattr(result, 'observation'), "StepResult missing observation"
            assert hasattr(result, 'reward'), "StepResult missing reward"
            assert hasattr(result, 'done'), "StepResult missing done"
            assert hasattr(result, 'info'), "StepResult missing info"
            
            self.log("step() returns valid StepResult", True, 
                    f"reward={result.reward}, done={result.done}")
            return True
        except Exception as e:
            self.log("step() returns valid StepResult", False, str(e))
            return False
    
    def test_state_returns_dict(self):
        """Test that state() returns internal state dict."""
        try:
            self.env.reset("task_1")
            state = self.env.state()
            assert isinstance(state, dict), "state() must return dict"
            assert 'task_id' in state, "state missing task_id"
            assert 'current_step' in state, "state missing current_step"
            self.log("state() returns valid dict", True, 
                    f"keys={list(state.keys())[:5]}")
            return True
        except Exception as e:
            self.log("state() returns valid dict", False, str(e))
            return False
    
    def test_reward_range(self):
        """Test that rewards are always in [-1.0, 1.0]."""
        try:
            rewards = []
            
            # Test various actions
            for task_id in ["task_1", "task_2", "task_3"]:
                self.env.reset(task_id)
                
                # Invalid action (should give negative reward)
                action = TriageAction(
                    task_id=task_id,
                    action_type=ActionType.CLASSIFY,
                    patient_id="P999_INVALID",
                    value=3
                )
                result = self.env.step(action)
                rewards.append(result.reward)
                
                # Valid REQUEST_INFO
                self.env.reset(task_id)
                state = self.env.state()
                patient_id = list(state['patient_hidden_states'].keys())[0]
                
                action = TriageAction(
                    task_id=task_id,
                    action_type=ActionType.REQUEST_INFO,
                    patient_id=patient_id,
                    value=None
                )
                result = self.env.step(action)
                rewards.append(result.reward)
            
            # Check all rewards in range
            out_of_range = [r for r in rewards if r < -1.0 or r > 1.0]
            
            if out_of_range:
                self.log("reward range [-1.0, 1.0]", False, 
                        f"Out of range rewards: {out_of_range}")
                return False
            else:
                self.log("reward range [-1.0, 1.0]", True, 
                        f"All {len(rewards)} rewards in range. Min={min(rewards):.2f}, Max={max(rewards):.2f}")
                return True
        except Exception as e:
            self.log("reward range [-1.0, 1.0]", False, str(e))
            return False
    
    def test_episode_termination(self):
        """Test that episodes terminate correctly."""
        try:
            # Task 1 should terminate after CLASSIFY
            self.env.reset("task_1")
            state = self.env.state()
            patient_id = list(state['patient_hidden_states'].keys())[0]
            
            action = TriageAction(
                task_id="task_1",
                action_type=ActionType.CLASSIFY,
                patient_id=patient_id,
                value=3
            )
            result = self.env.step(action)
            
            if not result.done:
                self.log("episode termination on CLASSIFY", False, 
                        "Episode should end after classification in task_1")
                return False
            
            # Verify no further actions accepted
            result2 = self.env.step(action)
            if result2.reward != 0.0:
                self.log("episode termination blocks further actions", False,
                        f"Expected reward=0.0 after done, got {result2.reward}")
                return False
            
            self.log("episode termination works", True, 
                    "Task 1 terminates after CLASSIFY and blocks further actions")
            return True
        except Exception as e:
            self.log("episode termination works", False, str(e))
            return False
    
    def test_invalid_action_handling(self):
        """Test various invalid actions are properly rejected."""
        test_cases = []
        
        try:
            # Invalid patient ID
            self.env.reset("task_1")
            action = TriageAction(
                task_id="task_1",
                action_type=ActionType.CLASSIFY,
                patient_id="P_NONEXISTENT",
                value=3
            )
            result = self.env.step(action)
            test_cases.append(("Invalid patient ID", result.reward < 0, result.info))
            
            # Invalid ESI level (out of range)
            try:
                action = TriageAction(
                    task_id="task_1",
                    action_type=ActionType.CLASSIFY,
                    patient_id="P001",
                    value=10  # Invalid: should be 1-5
                )
                test_cases.append(("Invalid ESI level", False, "Should have raised validation error"))
            except Exception as e:
                test_cases.append(("Invalid ESI level", True, f"Validation caught: {str(e)[:50]}"))
            
            # Task mismatch
            self.env.reset("task_1")
            state = self.env.state()
            patient_id = list(state['patient_hidden_states'].keys())[0]
            
            action = TriageAction(
                task_id="task_2",  # Wrong task
                action_type=ActionType.CLASSIFY,
                patient_id=patient_id,
                value=3
            )
            result = self.env.step(action)
            test_cases.append(("Task ID mismatch", result.reward < 0 or 'error' in result.info, result.info))
            
            passed = all(tc[1] for tc in test_cases)
            details = "\n  ".join([f"{tc[0]}: {'✓' if tc[1] else '✗'}" for tc in test_cases])
            
            self.log("invalid action handling", passed, details)
            return passed
        except Exception as e:
            self.log("invalid action handling", False, str(e))
            return False
    
    def test_action_spam(self):
        """Test that spamming the same action doesn't break the environment."""
        try:
            self.env.reset("task_1")
            state = self.env.state()
            patient_id = list(state['patient_hidden_states'].keys())[0]
            
            # Spam REQUEST_INFO 10 times
            action = TriageAction(
                task_id="task_1",
                action_type=ActionType.REQUEST_INFO,
                patient_id=patient_id,
                value=None
            )
            
            results = []
            for _ in range(10):
                result = self.env.step(action)
                results.append((result.reward, result.done))
            
            # Should not crash and should eventually either block or accumulate penalties
            self.log("action spam resilience", True, 
                    f"Processed 10 REQUEST_INFO actions. Last reward={results[-1][0]}")
            return True
        except Exception as e:
            self.log("action spam resilience", False, str(e))
            return False
    
    def test_repeated_reset(self):
        """Test that reset() can be called multiple times."""
        try:
            for i in range(5):
                obs = self.env.reset("task_1")
                assert obs.current_step == 0, f"Reset {i}: current_step should be 0"
            
            self.log("repeated reset()", True, "Successfully reset 5 times")
            return True
        except Exception as e:
            self.log("repeated reset()", False, str(e))
            return False
    
    def test_all_tasks_exist(self):
        """Test that all 3 tasks can be initialized."""
        try:
            for task_id in ["task_1", "task_2", "task_3"]:
                obs = self.env.reset(task_id)
                assert obs.task_id == task_id, f"Task ID mismatch for {task_id}"
            
            self.log("all tasks exist", True, "task_1, task_2, task_3 all initialize")
            return True
        except Exception as e:
            self.log("all tasks exist", False, str(e))
            return False
    
    def run_all(self):
        """Run all structural validation tests."""
        print("\n" + "="*60)
        print("PHASE 1 — STRUCTURAL VALIDATION")
        print("="*60 + "\n")
        
        tests = [
            self.test_all_tasks_exist,
            self.test_reset_returns_observation,
            self.test_step_returns_stepresult,
            self.test_state_returns_dict,
            self.test_reward_range,
            self.test_episode_termination,
            self.test_invalid_action_handling,
            self.test_action_spam,
            self.test_repeated_reset,
        ]
        
        for test in tests:
            test()
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {passed}/{total} tests passed")
        print(f"{'='*60}\n")
        
        return self.results

if __name__ == "__main__":
    validator = StructuralValidator()
    results = validator.run_all()
    
    # Save results
    with open('/home/vedu/Work/Env_Cravers/triage_env/reports/phase1_results.json', 'w') as f:
        json.dump(results, f, indent=2)
