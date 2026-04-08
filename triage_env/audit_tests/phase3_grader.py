#!/usr/bin/env python3
"""
PHASE 3 — GRADER VALIDATION
Tests grader determinism, reproducibility, and score ranges.
"""
import sys
sys.path.insert(0, '/home/vedu/Work/Env_Cravers/triage_env')

from app.environment import environment
from app.core.models.action import TriageAction, ActionType
import json

class GraderValidator:
    def __init__(self):
        self.env = environment
        self.results = {}
        
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
    
    def test_determinism(self, task_id: str, trajectory: list, runs: int = 10):
        """Test if grader produces same score for identical trajectory."""
        print(f"\n  Testing determinism for {task_id} ({runs} runs)...")
        
        scores = []
        details_list = []
        
        for i in range(runs):
            score_data = self.run_trajectory(task_id, trajectory)
            scores.append(score_data['score'])
            details_list.append(score_data['details'])
        
        # Check if all scores are identical
        unique_scores = set(scores)
        deterministic = len(unique_scores) == 1
        
        print(f"    Scores: {scores[:5]}... (showing first 5)")
        print(f"    Unique scores: {unique_scores}")
        print(f"    Status: {'✓ DETERMINISTIC' if deterministic else '✗ NON-DETERMINISTIC'}")
        
        return {
            "task_id": task_id,
            "deterministic": deterministic,
            "scores": scores,
            "unique_scores": list(unique_scores)
        }
    
    def test_score_range(self, task_id: str, num_trajectories: int = 10):
        """Test if scores are always in [0.0, 1.0]."""
        print(f"\n  Testing score range for {task_id} ({num_trajectories} trajectories)...")
        
        scores = []
        
        for i in range(num_trajectories):
            # Generate varied trajectories
            if task_id == "task_1":
                trajectory = [{
                    "task_id": task_id,
                    "action_type": "classify",
                    "patient_id": "P001",
                    "value": (i % 5) + 1  # Vary ESI levels
                }]
            elif task_id == "task_2":
                # Mix of actions
                trajectory = []
                for j in range(min(5, i + 1)):
                    trajectory.append({
                        "task_id": task_id,
                        "action_type": "request_info" if j % 2 == 0 else "classify",
                        "patient_id": f"P00{(j % 3) + 1}",
                        "value": None if j % 2 == 0 else ((j % 5) + 1)
                    })
            elif task_id == "task_3":
                # Resource assignments
                resources = ["trauma_bay", "bed_1", "bed_2", "bed_3", "doctor_1", "doctor_2", "discharge_area"]
                trajectory = []
                for j in range(min(5, i + 1)):
                    trajectory.append({
                        "task_id": task_id,
                        "action_type": "assign",
                        "patient_id": f"P00{(j % 5) + 1}",
                        "value": resources[j % len(resources)]
                    })
            
            try:
                score_data = self.run_trajectory(task_id, trajectory)
                scores.append(score_data['score'])
            except Exception as e:
                print(f"    Trajectory {i} failed: {e}")
                scores.append(None)
        
        # Filter out None scores
        valid_scores = [s for s in scores if s is not None]
        
        # Check range
        out_of_range = [s for s in valid_scores if s < 0.0 or s > 1.0]
        in_range = len(out_of_range) == 0
        
        print(f"    Scores: {[f'{s:.3f}' for s in valid_scores[:5]]}... (showing first 5)")
        print(f"    Min: {min(valid_scores):.3f}, Max: {max(valid_scores):.3f}")
        print(f"    Out of range: {out_of_range}")
        print(f"    Status: {'✓ ALL IN RANGE [0.0, 1.0]' if in_range else '✗ RANGE VIOLATION'}")
        
        return {
            "task_id": task_id,
            "in_range": in_range,
            "scores": valid_scores,
            "min": min(valid_scores) if valid_scores else None,
            "max": max(valid_scores) if valid_scores else None,
            "out_of_range": out_of_range
        }
    
    def test_score_differences(self, task_id: str):
        """Test if different trajectories produce meaningfully different scores."""
        print(f"\n  Testing score differentiation for {task_id}...")
        
        # Create clearly different trajectories
        if task_id == "task_1":
            trajectories = [
                # Perfect classification
                [{"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 3}],
                # Wrong classification (will check actual true ESI)
                [{"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 1}],
                # With info request
                [
                    {"task_id": task_id, "action_type": "request_info", "patient_id": "P001", "value": None},
                    {"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 3}
                ]
            ]
        elif task_id == "task_2":
            trajectories = [
                # Just one classification
                [{"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 2}],
                # Multiple info requests then classify
                [
                    {"task_id": task_id, "action_type": "request_info", "patient_id": "P001", "value": None},
                    {"task_id": task_id, "action_type": "request_info", "patient_id": "P002", "value": None},
                    {"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 2}
                ]
            ]
        elif task_id == "task_3":
            trajectories = [
                # Assign to trauma bay
                [{"task_id": task_id, "action_type": "assign", "patient_id": "P001", "value": "trauma_bay"}],
                # Assign to discharge
                [{"task_id": task_id, "action_type": "assign", "patient_id": "P001", "value": "discharge_area"}],
                # Assign to bed
                [{"task_id": task_id, "action_type": "assign", "patient_id": "P001", "value": "bed_1"}]
            ]
        
        scores = []
        for i, traj in enumerate(trajectories):
            score_data = self.run_trajectory(task_id, traj)
            scores.append(score_data['score'])
            print(f"    Trajectory {i+1}: score = {score_data['score']:.3f}")
        
        # Check if scores differ
        unique_scores = len(set(scores))
        differentiation = unique_scores > 1
        
        print(f"    Unique scores: {unique_scores}/{len(scores)}")
        print(f"    Status: {'✓ MEANINGFUL DIFFERENTIATION' if differentiation else '✗ NO DIFFERENTIATION'}")
        
        return {
            "task_id": task_id,
            "differentiation": differentiation,
            "scores": scores,
            "unique_scores": unique_scores
        }
    
    def run_all(self):
        """Run all grader validation tests."""
        print("\n" + "="*60)
        print("PHASE 3 — GRADER VALIDATION")
        print("="*60 + "\n")
        
        tasks = ["task_1", "task_2", "task_3"]
        
        for task_id in tasks:
            print(f"\n{'='*60}")
            print(f"Testing graders for {task_id}")
            print(f"{'='*60}")
            
            # Simple trajectory for determinism test
            if task_id == "task_1":
                trajectory = [{"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 3}]
            elif task_id == "task_2":
                trajectory = [{"task_id": task_id, "action_type": "classify", "patient_id": "P001", "value": 2}]
            elif task_id == "task_3":
                trajectory = [{"task_id": task_id, "action_type": "assign", "patient_id": "P001", "value": "bed_1"}]
            
            # Run tests
            det_result = self.test_determinism(task_id, trajectory, runs=10)
            range_result = self.test_score_range(task_id, num_trajectories=10)
            diff_result = self.test_score_differences(task_id)
            
            self.results[task_id] = {
                "determinism": det_result,
                "score_range": range_result,
                "differentiation": diff_result
            }
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}\n")
        
        for task_id in tasks:
            res = self.results[task_id]
            print(f"{task_id}:")
            print(f"  Deterministic: {'✓' if res['determinism']['deterministic'] else '✗'}")
            print(f"  Score range [0,1]: {'✓' if res['score_range']['in_range'] else '✗'}")
            print(f"  Differentiates: {'✓' if res['differentiation']['differentiation'] else '✗'}")
        
        # Save results
        with open('/home/vedu/Work/Env_Cravers/triage_env/reports/phase3_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results

if __name__ == "__main__":
    validator = GraderValidator()
    validator.run_all()
