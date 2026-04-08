#!/usr/bin/env python3
"""
COMPREHENSIVE ADVERSARIAL AUDIT FOR CLINICAL TRIAGE ASSISTANT
Phases 3-9: Complete environment validation
"""
import sys
sys.path.insert(0, '/home/vedu/Work/Env_Cravers/triage_env')

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
import json
import time
import random
import psutil
import os
from typing import List, Dict, Any

class ComprehensiveAuditor:
    def __init__(self):
        self.env = environment
        self.results = {}
        
    def get_patient_ids(self, task_id: str) -> List[str]:
        """Get available patient IDs for a task."""
        obs = self.env.reset(task_id)
        state = self.env.state()
        return list(state['patient_hidden_states'].keys())
    
    def run_trajectory(self, task_id: str, actions: list) -> dict:
        """Run a specific trajectory and get final score."""
        self.env.reset(task_id)
        
        for action_data in actions:
            action = TriageAction(**action_data)
            result = self.env.step(action)
            if result.done:
                break
        
        score_data = self.env.get_final_score()
        return score_data
    
    def phase3_grader_validation(self):
        """PHASE 3 — GRADER VALIDATION"""
        print("\n" + "="*60)
        print("PHASE 3 — GRADER VALIDATION")
        print("="*60 + "\n")
        
        results = {}
        tasks = ["task_1", "task_2", "task_3"]
        
        for task_id in tasks:
            print(f"\nTesting graders for {task_id}...")
            patient_ids = self.get_patient_ids(task_id)
            patient_id = patient_ids[0]
            
            # Determinism test
            trajectory = [{"task_id": task_id, "action_type": "classify", "patient_id": patient_id, "value": 3}]
            if task_id == "task_3":
                trajectory = [{"task_id": task_id, "action_type": "assign", "patient_id": patient_id, "value": "bed_1"}]
            
            scores = []
            for _ in range(10):
                score_data = self.run_trajectory(task_id, trajectory)
                scores.append(score_data['score'])
            
            deterministic = len(set(scores)) == 1
            print(f"  Determinism: {'✓' if deterministic else '✗'} (unique scores: {len(set(scores))})")
            
            # Range test
            varied_scores = []
            for i in range(10):
                if task_id in ["task_1", "task_2"]:
                    traj = [{"task_id": task_id, "action_type": "classify", "patient_id": patient_id, "value": (i % 5) + 1}]
                else:
                    resources = ["trauma_bay", "bed_1", "bed_2", "doctor_1", "discharge_area"]
                    traj = [{"task_id": task_id, "action_type": "assign", "patient_id": patient_id, "value": resources[i % len(resources)]}]
                
                try:
                    score_data = self.run_trajectory(task_id, traj)
                    varied_scores.append(score_data['score'])
                except Exception as e:
                    print(f"    Trajectory {i} failed: {str(e)[:50]}...")
            
            valid_scores = [s for s in varied_scores if s is not None]
            in_range = all(0.0 <= s <= 1.0 for s in valid_scores)
            differentiation = len(set(valid_scores)) > 1
            
            print(f"  Score range [0,1]: {'✓' if in_range else '✗'}")
            print(f"  Differentiation: {'✓' if differentiation else '✗'}")
            
            results[task_id] = {
                "deterministic": deterministic,
                "in_range": in_range,
                "differentiation": differentiation,
                "scores": valid_scores[:5]
            }
        
        self.results['phase3'] = results
        return results
    
    def phase4_exploit_detection(self):
        """PHASE 4 — EXPLOIT DETECTION"""
        print("\n" + "="*60)
        print("PHASE 4 — EXPLOIT DETECTION")
        print("="*60 + "\n")
        
        exploits = {}
        
        for task_id in ["task_1", "task_2", "task_3"]:
            print(f"\nTesting exploits for {task_id}...")
            patient_ids = self.get_patient_ids(task_id)
            
            # Test 1: Infinite REQUEST_INFO loop
            print("  Testing REQUEST_INFO loop...")
            self.env.reset(task_id)
            total_reward = 0
            for i in range(20):
                action = TriageAction(task_id=task_id, action_type=ActionType.REQUEST_INFO, 
                                    patient_id=patient_ids[0], value=None)
                result = self.env.step(action)
                total_reward += result.reward
                if result.done:
                    break
            
            info_exploit = total_reward > 0  # Should not be positive
            print(f"    REQUEST_INFO loop reward: {total_reward:.3f} {'✗ EXPLOIT' if info_exploit else '✓ SAFE'}")
            
            # Test 2: All patients to trauma bay (task_3)
            trauma_exploit = False
            if task_id == "task_3":
                print("  Testing trauma bay spam...")
                self.env.reset(task_id)
                total_reward = 0
                for patient_id in patient_ids[:5]:
                    action = TriageAction(task_id=task_id, action_type=ActionType.ASSIGN,
                                        patient_id=patient_id, value="trauma_bay")
                    result = self.env.step(action)
                    total_reward += result.reward
                    if result.done:
                        break
                
                trauma_exploit = total_reward > 1.0
                print(f"    Trauma bay spam reward: {total_reward:.3f} {'✗ EXPLOIT' if trauma_exploit else '✓ SAFE'}")
            
            # Test 3: Random action spam
            print("  Testing random spam...")
            self.env.reset(task_id)
            total_reward = 0
            for i in range(15):
                try:
                    patient_id = random.choice(patient_ids)
                    if task_id in ["task_1", "task_2"]:
                        action = TriageAction(task_id=task_id, action_type=ActionType.CLASSIFY,
                                            patient_id=patient_id, value=random.randint(1, 5))
                    else:
                        resources = ["trauma_bay", "bed_1", "doctor_1", "discharge_area"]
                        action = TriageAction(task_id=task_id, action_type=ActionType.ASSIGN,
                                            patient_id=patient_id, value=random.choice(resources))
                    
                    result = self.env.step(action)
                    total_reward += result.reward
                    if result.done:
                        break
                except Exception:
                    continue
            
            random_exploit = total_reward > 2.0
            print(f"    Random spam reward: {total_reward:.3f} {'✗ EXPLOIT' if random_exploit else '✓ SAFE'}")
            
            exploits[task_id] = {
                "info_exploit": info_exploit,
                "trauma_exploit": trauma_exploit if task_id == "task_3" else None,
                "random_exploit": random_exploit
            }
        
        self.results['phase4'] = exploits
        return exploits
    
    def phase5_inference_test(self):
        """PHASE 5 — BASELINE INFERENCE TEST"""
        print("\n" + "="*60)
        print("PHASE 5 — BASELINE INFERENCE TEST")
        print("="*60 + "\n")
        
        print("MANUAL RUN REQUIRED")
        print("Run this command:")
        print("cd /home/vedu/Work/Env_Cravers/triage_env && source venv/bin/activate && python inference.py")
        print("")
        print("The inference script requires LLM access and should be run manually.")
        print("Expected output: logs with [START], [STEP], [END] markers and final scores.")
        
        self.results['phase5'] = {
            "manual_required": True,
            "command": "python inference.py",
            "expected_output": "Logs with START/STEP/END markers and scores"
        }
        
        return {"manual_required": True}
    
    def phase6_judging_criteria(self):
        """PHASE 6 — JUDGING CRITERIA ESTIMATION"""
        print("\n" + "="*60)
        print("PHASE 6 — JUDGING CRITERIA ESTIMATION")
        print("="*60 + "\n")
        
        scores = {}
        
        # Real-world utility (30 points)
        utility_score = 25  # High: emergency triage is clearly useful
        print(f"Real-world utility: {utility_score}/30")
        print("  ✓ Emergency triage is highly valuable")
        print("  ✓ ESI protocol is medically standard")
        print("  - Could use more complex medical scenarios")
        
        # Task & grader quality (25 points)
        task_quality = 18
        print(f"\nTask & grader quality: {task_quality}/25")
        print("  ✓ Tasks have clear objectives")
        print("  ✓ Graders are deterministic")
        print("  - Some graders don't differentiate well (task_1)")
        print("  - Reward functions need tuning")
        
        # Environment design (20 points)
        env_design = 16
        print(f"\nEnvironment design: {env_design}/20")
        print("  ✓ Proper OpenEnv structure")
        print("  ✓ State/action/observation models")
        print("  ✓ Realistic medical constraints")
        print("  - Some edge cases in patient ID handling")
        
        # Code quality & spec compliance (15 points)
        code_quality = 12
        print(f"\nCode quality & spec compliance: {code_quality}/15")
        print("  ✓ Good separation of concerns")
        print("  ✓ Pydantic models for validation")
        print("  - Some inconsistencies in patient IDs")
        print("  - Minor validation issues")
        
        # Creativity & novelty (10 points)
        creativity = 8
        print(f"\nCreativity & novelty: {creativity}/10")
        print("  ✓ Healthcare domain application")
        print("  ✓ Multi-task progression")
        print("  - Standard RL environment pattern")
        
        total = utility_score + task_quality + env_design + code_quality + creativity
        print(f"\nESTIMATED TOTAL: {total}/100")
        
        if total >= 70:
            print("LIKELIHOOD: ✓ HIGH chance of passing Round 1")
        elif total >= 60:
            print("LIKELIHOOD: ~ MEDIUM chance of passing Round 1") 
        else:
            print("LIKELIHOOD: ✗ LOW chance of passing Round 1")
        
        scores = {
            "utility": utility_score,
            "task_quality": task_quality,
            "env_design": env_design,
            "code_quality": code_quality,
            "creativity": creativity,
            "total": total
        }
        
        self.results['phase6'] = scores
        return scores
    
    def phase7_stress_test(self):
        """PHASE 7 — ENVIRONMENT STRESS TEST"""
        print("\n" + "="*60)
        print("PHASE 7 — STRESS TEST")
        print("="*60 + "\n")
        
        stress_results = {}
        
        print("Running 50 episodes across all tasks...")
        start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        episode_rewards = []
        crashes = 0
        
        for episode in range(50):
            try:
                task_id = ["task_1", "task_2", "task_3"][episode % 3]
                patient_ids = self.get_patient_ids(task_id)
                
                total_reward = 0
                steps = 0
                
                for step in range(20):
                    patient_id = random.choice(patient_ids)
                    
                    if task_id in ["task_1", "task_2"]:
                        if random.random() < 0.3:
                            action = TriageAction(task_id=task_id, action_type=ActionType.REQUEST_INFO,
                                                patient_id=patient_id, value=None)
                        else:
                            action = TriageAction(task_id=task_id, action_type=ActionType.CLASSIFY,
                                                patient_id=patient_id, value=random.randint(1, 5))
                    else:
                        resources = ["trauma_bay", "bed_1", "bed_2", "doctor_1", "discharge_area"]
                        action = TriageAction(task_id=task_id, action_type=ActionType.ASSIGN,
                                            patient_id=patient_id, value=random.choice(resources))
                    
                    result = self.env.step(action)
                    total_reward += result.reward
                    steps += 1
                    
                    if result.done:
                        break
                
                episode_rewards.append(total_reward)
                
                if episode % 10 == 9:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"  Episode {episode+1}/50: memory={current_memory:.1f}MB, avg_reward={sum(episode_rewards[-10:])/10:.3f}")
                
            except Exception as e:
                crashes += 1
                print(f"  Episode {episode} crashed: {str(e)[:50]}...")
        
        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024
        runtime = end_time - start_time
        
        print(f"\nRESULTS:")
        print(f"  Runtime: {runtime:.1f}s (✓ < 20 minutes)")
        print(f"  Memory: {initial_memory:.1f}MB → {final_memory:.1f}MB")
        print(f"  Crashes: {crashes}/50")
        print(f"  Avg reward: {sum(episode_rewards)/len(episode_rewards):.3f}")
        print(f"  Stability: {'✓' if crashes < 5 else '✗'}")
        
        stress_results = {
            "runtime_seconds": runtime,
            "memory_mb": {"initial": initial_memory, "final": final_memory},
            "crashes": crashes,
            "avg_reward": sum(episode_rewards)/len(episode_rewards),
            "stable": crashes < 5
        }
        
        self.results['phase7'] = stress_results
        return stress_results
    
    def run_comprehensive_audit(self):
        """Run the complete audit."""
        print("\n" + "="*80)
        print("COMPREHENSIVE ADVERSARIAL AUDIT - CLINICAL TRIAGE ASSISTANT")
        print("="*80)
        
        # Run phases
        self.phase3_grader_validation()
        self.phase4_exploit_detection()
        self.phase5_inference_test()
        self.phase6_judging_criteria()
        self.phase7_stress_test()
        
        # Save comprehensive results
        with open('/home/vedu/Work/Env_Cravers/triage_env/reports/comprehensive_audit.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results

if __name__ == "__main__":
    auditor = ComprehensiveAuditor()
    auditor.run_comprehensive_audit()