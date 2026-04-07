# triage_env/inference.py
import os
import json
import httpx
from openai import OpenAI
from typing import Optional

# Environment configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")

TASKS = ["task_1", "task_2", "task_3"]
MAX_STEPS = 30
TEMPERATURE = 0.0

def log_start(task: str, model: str):
    """Prints episode commencement log in standardized format."""
    print(f"[START] task={task} env=clinical-triage model={model}")

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str] = None):
    """Prints per-step transition log in standardized format."""
    err_str = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={err_str}")

def log_end(success: bool, steps: int, score: float, rewards: list[float]):
    """Prints episode results log in standardized format."""
    reward_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={reward_str}")

def get_llm_action(client: OpenAI, observation: dict, task_id: str) -> dict:
    """Invokes the LLM to decide the next triage action based on current state."""
    system_prompt = (
        "You are an emergency room triage agent. Given patient observations, "
        "you must take exactly one action per step. Respond ONLY with a valid "
        "JSON action object with fields: task_id, action_type, patient_id, value.\n"
        "Valid action_types: classify, reorder, assign, request_info, discharge.\n"
        "For classify: value must be 1-5 (ESI level).\n"
        "For assign: value must be a valid resource ID.\n"
        "For reorder: value must be a queue position integer."
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(observation)}
            ],
            temperature=TEMPERATURE
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # Safe default action on parsing or API failure
        p_id = observation["patients"][0]["patient_id"] if observation["patients"] else "unknown"
        return {"task_id": task_id, "action_type": "classify", "patient_id": p_id, "value": 3}

def run_task(task_id: str, client: OpenAI) -> tuple[float, list[float]]:
    """Runs one complete episode loop against the environment API."""
    rewards = []
    log_start(task_id, MODEL_NAME)
    
    try:
        # 1. Reset environment
        with httpx.Client(base_url=ENV_BASE_URL, timeout=30.0) as http_client:
            reset_resp = http_client.post("/reset", json={"task_id": task_id})
            reset_resp.raise_for_status()
            obs = reset_resp.json()
            
            # 2. Step loop
            for step in range(1, MAX_STEPS + 1):
                action = get_llm_action(client, obs, task_id)
                step_resp = http_client.post("/step", json=action)
                step_resp.raise_for_status()
                
                result = step_resp.json()
                obs = result["observation"]
                reward = result["reward"]
                done = result["done"]
                
                rewards.append(reward)
                log_step(step, action["action_type"], reward, done)
                
                if done:
                    break
            
            # 3. Final score
            score_resp = http_client.get("/score")
            score_resp.raise_for_status()
            final_score = score_resp.json()["score"]
            log_end(True, len(rewards), final_score, rewards)
            return final_score, rewards
            
    except Exception as e:
        log_step(max(1, len(rewards)), "error", 0.0, True, str(e))
        log_end(False, len(rewards), 0.0, rewards)
        return 0.0, rewards

def main():
    """Sequential execution of all environment benchmark tasks."""
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for task_id in TASKS:
        run_task(task_id, client)

if __name__ == "__main__":
    main()
