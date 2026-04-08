import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        print("--- Testing /reset ---")
        reset_resp = client.post("/reset", json={"task_id": "task_1"})
        print(f"Status: {reset_resp.status_code}")
        obs = reset_resp.json()
        print(f"Observation keys: {list(obs.keys())}")
        
        print("\n--- Testing /step ---")
        patient_id = obs["patients"][0]["patient_id"]
        step_resp = client.post("/step", json={
            "task_id": "task_1",
            "action_type": "classify",
            "patient_id": patient_id,
            "value": 3
        })
        print(f"Status: {step_resp.status_code}")
        result = step_resp.json()
        print(f"Reward: {result['reward']}")
        print(f"Info: {json.dumps(result['info'], indent=2)}")
        
        print("\n--- Testing /score ---")
        score_resp = client.get("/score")
        print(f"Status: {score_resp.status_code}")
        score_result = score_resp.json()
        print(f"Score Result: {json.dumps(score_result, indent=2)}")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"Error: {e}")
