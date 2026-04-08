#!/usr/bin/env python3
"""
PHASE 2 — REWARD FUNCTION AUDIT
Tests whether rewards are truly dynamic and meaningful.
"""
import sys
sys.path.insert(0, '/home/vedu/Work/Env_Cravers/triage_env')

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
import random
import json
from typing import List, Tuple

class RewardAuditor:
    def __init__(self):
        self.env = environment
        self.results = {}
        
    def run_episode(self, task_id: str, policy: str) -> dict:
        """Run a full episode with a given policy."""
        obs = self.env.reset(task_id)
        total_reward = 0.0
        steps = 0
        rewards = []
        completed = False
        
        max_steps = 30
        
        while steps < max_steps:
            state = self.env.state()
            
            if state.get('episode_done', False):
                completed = True
                break
            
            # Get available patients
            patient_ids = list(state['patient_hidden_states'].keys())
            if not patient_ids:
                break
            
            # Generate action based on policy
            action = self._generate_action(task_id, policy, patient_ids, state, steps)
            
            if action is None:
                break
            
            result = self.env.step(action)
            rewards.append(result.reward)
            total_reward += result.reward
            steps += 1
            
            if result.done:
                completed = True
                break
        
        return {
            "policy": policy,
            "task_id": task_id,
            "total_reward": total_reward,
            "avg_reward": total_reward / max(1, steps),
            "steps": steps,
            "completed": completed,
            "reward_variance": self._variance(rewards),
            "min_reward": min(rewards) if rewards else 0,
            "max_reward": max(rewards) if rewards else 0,
            "rewards": rewards
        }
    
    def _generate_action(self, task_id: str, policy: str, patient_ids: List[str], state: dict, step: int):
        """Generate action based on policy type."""
        
        if policy == "perfect":
            # Try to make optimal decisions using hidden state
            patient_id = patient_ids[0]
            hidden = state['patient_hidden_states'][patient_id]
            
            if task_id == "task_1":
                # Perfect classification
                true_esi = hidden['true_esi_level']
                return TriageAction(
                    task_id=task_id,
                    action_type=ActionType.CLASSIFY,
                    patient_id=patient_id,
                    value=true_esi
                )
            elif task_id == "task_2":
                # Request info first, then classify correctly
                if step == 0:
                    return TriageAction(
                        task_id=task_id,
                        action_type=ActionType.REQUEST_INFO,
                        patient_id=patient_id,
                        value=None
                    )
                else:
                    true_esi = hidden['true_esi_level']
                    return TriageAction(
                        task_id=task_id,
                        action_type=ActionType.CLASSIFY,
                        patient_id=patient_id,
                        value=true_esi
                    )
            elif task_id == "task_3":
                # Assign to optimal resource
                if step == 0:
                    return TriageAction(
                        task_id=task_id,
                        action_type=ActionType.REQUEST_INFO,
                        patient_id=patient_id,
                        value=None
                    )
                else:
                    optimal_resource = hidden.get('optimal_resource')
                    if optimal_resource:
                        return TriageAction(
                            task_id=task_id,
                            action_type=ActionType.ASSIGN,
                            patient_id=patient_id,
                            value=optimal_resource
                        )
                    else:
                        return TriageAction(
                            task_id=task_id,
                            action_type=ActionType.CLASSIFY,
                            patient_id=patient_id,
                            value=hidden['true_esi_level']
                        )
        
        elif policy == "random":
            # Random valid actions
            patient_id = random.choice(patient_ids)
            
            if task_id == "task_1":
                return TriageAction(
                    task_id=task_id,
                    action_type=ActionType.CLASSIFY,
                    patient_id=patient_id,
                    value=random.randint(1, 5)
                )
            elif task_id == "task_2":
                if random.random() < 0.3:
                    return TriageAction(
                        task_id=task_id,
                        action_type=ActionType.CLASSIFY,
                        patient_id=patient_id,
                        value=random.randint(1, 5)
                    )
                else:
                    return TriageAction(
                        task_id=task_id,
                        action_type=ActionType.REQUEST_INFO,
                        patient_id=patient_id,
                        value=None
                    )
            elif task_id == "task_3":
                resources = ["doctor_1", "doctor_2", "bed_1", "bed_2", "bed_3", "trauma_bay", "discharge_area"]
                return TriageAction(
                    task_id=task_id,
                    action_type=ActionType.ASSIGN,
                    patient_id=patient_id,
                    value=random.choice(resources)
                )
        
        elif policy == "always_low":
            # Always classify as ESI 5 (lowest urgency)
            patient_id = patient_ids[0]
            return TriageAction(
                task_id=task_id,
                action_type=ActionType.CLASSIFY,
                patient_id=patient_id,
                value=5
            )
        
        elif policy == "always_critical":
            # Always classify as ESI 1 (highest urgency)
            patient_id = patient_ids[0]
            return TriageAction(
                task_id=task_id,
                action_type=ActionType.CLASSIFY,
                patient_id=patient_id,
                value=1
            )
        
        elif policy == "noop":
            # Just request info repeatedly
            patient_id = patient_ids[0]
            return TriageAction(
                task_id=task_id,
                action_type=ActionType.REQUEST_INFO,
                patient_id=patient_id,
                value=None
            )
        
        return None
    
    def _variance(self, values: List[float]) -> float:
        """Calculate variance of a list."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def run_all(self):
        """Run reward audit across all tasks and policies."""
        print("\n" + "="*60)
        print("PHASE 2 — REWARD FUNCTION AUDIT")
        print("="*60 + "\n")
        
        policies = ["perfect", "random", "always_low", "always_critical", "noop"]
        tasks = ["task_1", "task_2", "task_3"]
        
        all_results = []
        
        for task_id in tasks:
            print(f"\n--- Testing {task_id} ---")
            task_results = {}
            
            for policy in policies:
                print(f"  Running {policy} policy...", end=" ")
                result = self.run_episode(task_id, policy)
                task_results[policy] = result
                all_results.append(result)
                print(f"reward={result['total_reward']:.3f}, steps={result['steps']}")
            
            self.results[task_id] = task_results
        
        # Analysis
        print("\n" + "="*60)
        print("ANALYSIS")
        print("="*60 + "\n")
        
        for task_id in tasks:
            print(f"\n{task_id}:")
            task_res = self.results[task_id]
            
            perfect_reward = task_res["perfect"]["total_reward"]
            random_reward = task_res["random"]["total_reward"]
            low_reward = task_res["always_low"]["total_reward"]
            critical_reward = task_res["always_critical"]["total_reward"]
            noop_reward = task_res["noop"]["total_reward"]
            
            print(f"  Perfect:   {perfect_reward:+.3f}")
            print(f"  Random:    {random_reward:+.3f}")
            print(f"  Always-Low: {low_reward:+.3f}")
            print(f"  Always-Critical: {critical_reward:+.3f}")
            print(f"  No-op:     {noop_reward:+.3f}")
            
            # Verify good policies > bad policies
            verification = perfect_reward > random_reward and perfect_reward > noop_reward
            status = "✓ PASS" if verification else "✗ FAIL"
            print(f"\n  {status}: Perfect > Random/NoOp")
            
            # Check reward variance
            variances = [task_res[p]["reward_variance"] for p in policies]
            avg_variance = sum(variances) / len(variances)
            print(f"  Avg reward variance: {avg_variance:.4f}")
        
        # Save results
        with open('/home/vedu/Work/Env_Cravers/triage_env/reports/phase2_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results

if __name__ == "__main__":
    auditor = RewardAuditor()
    auditor.run_all()
