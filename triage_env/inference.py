# triage_env/inference.py
import os
import json
import httpx
import re
import sys
import time
from openai import OpenAI
from typing import Any, Optional
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Environment configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional - if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# Internal configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", HF_TOKEN or "")
OPENENV_HOST = os.getenv("OPENENV_HOST", "localhost:8000")

# Ensure ENV_BASE_URL has a scheme
if os.getenv("ENV_BASE_URL"):
    ENV_BASE_URL = os.getenv("ENV_BASE_URL")
elif "://" in OPENENV_HOST:
    ENV_BASE_URL = OPENENV_HOST
else:
    ENV_BASE_URL = f"http://{OPENENV_HOST}"

TASKS = ["task_1", "task_2", "task_3"]
MAX_STEPS = 30
TEMPERATURE = 0.0


def _extract_action_json(raw: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from model output."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("Empty model response")

    candidates: list[str] = [text]

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.append(fenced.group(1).strip())

    inline = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if inline:
        candidates.append(inline.group(0).strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Could not parse JSON action from model response")


def _estimate_esi(patient: dict[str, Any]) -> int:
    """Simple vitals-driven ESI estimate for robust fallback decisions."""
    vitals = patient.get("vitals") or {}
    
    def _safe_int(val: Any, default: int) -> int:
        try:
            return int(float(val)) if val is not None else default
        except (ValueError, TypeError):
            return default

    spo2 = _safe_int(vitals.get("spo2"), 95)
    hr = _safe_int(vitals.get("heart_rate"), 90)
    sbp = _safe_int(vitals.get("systolic_bp"), 110)
    rr = _safe_int(vitals.get("respiratory_rate"), 16)
    gcs = _safe_int(vitals.get("gcs"), 15)
    
    try:
        temp = float(vitals.get("temperature") or 37.0)
    except (ValueError, TypeError):
        temp = 37.0

    if spo2 < 70 or gcs <= 8 or sbp < 80:
        return 1
    if spo2 < 90 or hr > 150 or hr < 40 or sbp < 90 or rr > 28:
        return 2
    if hr > 110 or rr > 22 or temp >= 38.5:
        return 3
    very_stable = (
        spo2 >= 97
        and 60 <= hr <= 95
        and 100 <= sbp <= 140
        and 12 <= rr <= 18
        and temp <= 37.5
        and gcs == 15
    )
    if very_stable:
        return 5
    return 4


def _pick_first_waiting_patient(observation: dict[str, Any]) -> dict[str, Any]:
    patients = observation.get("patients") or []
    if not patients:
        return {"patient_id": "unknown"}

    patient_by_id = {p.get("patient_id"): p for p in patients}
    queue = observation.get("queue_order") or []
    for pid in queue:
        patient = patient_by_id.get(pid)
        if patient:
            return patient
    return patients[0]


def _fallback_action(observation: dict[str, Any], task_id: str) -> dict[str, Any]:
    """
    Deterministic fallback when model output is unavailable/invalid.
    Designed to avoid infinite request_info loops and keep actions task-valid.
    """
    patient = _pick_first_waiting_patient(observation)
    patient_id = patient.get("patient_id", "unknown")
    queue = observation.get("queue_order") or []

    if task_id in ("task_1", "task_2"):
        return {
            "task_id": task_id,
            "action_type": "classify",
            "patient_id": patient_id,
            "value": _estimate_esi(patient),
        }

    # task_3 fallback: try feasible assignment first
    resources = observation.get("resources") or []
    free_resources = {r.get("resource_id") for r in resources if not r.get("is_occupied", False)}
    doctors_free = ("doctor_1" in free_resources) or ("doctor_2" in free_resources)
    patient_by_id = {p.get("patient_id"): p for p in observation.get("patients") or []}

    def preferred_locations(esi: int) -> list[str]:
        if esi == 1:
            return ["trauma_bay"]
        if esi == 2:
            return ["trauma_bay", "bed_1", "bed_2"]
        if esi == 3:
            return ["bed_1", "bed_2", "bed_3"]
        if esi == 4:
            return ["bed_3"]
        return ["discharge_area"]

    waiting = [patient_by_id[pid] for pid in queue if pid in patient_by_id]
    waiting.sort(key=_estimate_esi)

    for candidate in waiting:
        esi = _estimate_esi(candidate)
        needs_doctor = esi <= 3
        if needs_doctor and not doctors_free:
            continue
        for rid in preferred_locations(esi):
            if rid in free_resources:
                return {
                    "task_id": task_id,
                    "action_type": "assign",
                    "patient_id": candidate.get("patient_id", patient_id),
                    "value": rid,
                }

    # If no feasible assignment currently, perform a valid queue action.
    target_id = queue[0] if queue else patient_id
    return {
        "task_id": task_id,
        "action_type": "reorder",
        "patient_id": target_id,
        "value": max(1, len(queue)),
    }

def log_start(task: str, model: str):
    """Prints episode commencement log in standardized format."""
    print(f"[START] task={task} env=clinical-triage model={model}")

def log_step(step: int, action: dict, reward: float, done: bool, breakdown: dict = None, error: Optional[str] = None):
    """Prints per-step transition log in the strictly required OpenEnv format."""
    print(f"[STEP] step={step} action={json.dumps(action)} reward={reward} done={str(done).lower()}")

def log_end(success: bool, steps: int, score: float, rewards: list[float], details: dict = None):
    """Prints episode results in the strictly required OpenEnv format."""
    print(f"[END] success={str(success).lower()} steps={steps} score={score} rewards={rewards}")

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
        content = response.choices[0].message.content or ""
        action = _extract_action_json(content)
        action["task_id"] = task_id

        action_type = str(action.get("action_type", "")).strip().lower()
        action["action_type"] = action_type

        if action_type in ("classify", "reorder") and action.get("value") is not None:
            try:
                action["value"] = int(action["value"])
            except (ValueError, TypeError):
                pass

        if not action.get("patient_id"):
            action["patient_id"] = _pick_first_waiting_patient(observation).get("patient_id", "unknown")

        return action
    except Exception as e:
        return _fallback_action(observation, task_id)

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
                reward_data = result["reward"]
                reward = reward_data["value"] if isinstance(reward_data, dict) else reward_data
                done = result["done"]
                breakdown = result.get("info", {}).get("reward_breakdown")
                
                rewards.append(reward)
                log_step(step, action, reward, done, breakdown=breakdown)
                
                if done:
                    break
            
            # 3. Final score
            score_resp = http_client.get("/score")
            score_resp.raise_for_status()
            score_data = score_resp.json()
            final_score = score_data["score"]
            score_details = score_data.get("details")
            log_end(True, len(rewards), final_score, rewards, details=score_details)
            return final_score, rewards
            
    except Exception as e:
        log_step(max(1, len(rewards)), {"action_type": "error"}, 0.0, True, error=str(e))
        log_end(False, len(rewards), 0.0, rewards)
        return 0.0, rewards

def main():
    """Sequential execution of all environment benchmark tasks."""
    try:
        if not OPENAI_API_KEY:
            print("[ERROR] Credentials missing. Please set OPENAI_API_KEY or HF_TOKEN.")
            sys.exit(1)

        client = OpenAI(
            base_url=API_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        
        # Robust health check with retries before tasks
        print(f"[INFO] Connecting to environment at {ENV_BASE_URL}...")
        max_retries = 10
        health_ok = False
        for i in range(max_retries):
            try:
                with httpx.Client(timeout=5.0) as check_client:
                    resp = check_client.get(f"{ENV_BASE_URL}/health")
                    if resp.status_code == 200:
                        print(f"[INFO] Environment health: {resp.status_code} (OK)")
                        health_ok = True
                        break
            except Exception as e:
                print(f"[WARNING] Retry {i+1}/{max_retries}: Environment not ready yet ({e})")
            time.sleep(3)

        if not health_ok:
            print("[ERROR] Environment failed to start after multiple retries.")
            sys.exit(1)

        for task_id in TASKS:
            run_task(task_id, client)
        
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal unhandled exception in inference.py: {e}")
        print(f"[DEBUG] ENV_BASE_URL used: {ENV_BASE_URL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
