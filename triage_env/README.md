# Clinical Triage Assistant

An OpenEnv RL environment simulating emergency room triage decisions. Agents learn to classify patient urgency, manage waiting queues, and allocate scarce medical resources optimally based on the 5-level **Emergency Severity Index (ESI)** protocol.

## Environment Overview
In an Emergency Department, seconds save lives. This environment places an RL agent in the role of a Clinical Triage Officer. The agent must process incoming patients, identify critical deteriorations, and manage resources like doctors, beds, and trauma bays. It addresses the real-world complexity of clinical decision-making where information is partial, resources are fixed, and patient conditions are dynamic.

## Task Descriptions
| Task | Difficulty | Patients | Description | Max Steps |
| :--- | :--- | :--- | :--- | :--- |
| **task_1** | Easy | 1 | Classify one patient's ESI level from initial vitals. | 30 |
| **task_2** | Medium | 10 | Manage a waiting queue through classification and reordering. | 30 |
| **task_3** | Hard | 15 | Allocate doctors, beds, and trauma bays across a large queue. | 30 |

## Observation Space
The agent receives a structured `TriageObservation` containing:
- `task_id`: Identifier for the current task.
- `current_step`: Current step in the sequence.
- `elapsed_minutes`: Discrete simulation time (5m increments).
- `patients`: List of `PatientObservation` objects (ID, vitals, symptoms, delta flags).
- `resources`: List of `ResourceObservation` objects (ID, type, occupancy status).
- `queue_order`: current ordering of patients in the waiting queue.
- `episode_done`: Boolean termination flag.

## Action Space
| Action Type | Value | Task Applicability |
| :--- | :--- | :--- |
| `classify` | 1-5 (ESI) | task_1, task_2 |
| `reorder` | 1-N (Pos) | task_2, task_3 |
| `assign` | Resource ID | task_3 |
| `request_info` | N/A | All tasks (Unlocks history) |
| `discharge` | N/A | task_2, task_3 (Early discharge) |

## Reward Function
- **Positive Signals**: Correct classification (+0.6 to +1.0), optimal queue ordering (+0.1), correct resource allocation (+0.8), critical patient speed bonus (+0.1).
- **Negative Signals**: Incorrect classification (0 to +0.4), invalid action (-0.2), clinical deterioration (-0.5 per patient).

## API Credentials

# If using OpenAI directly
export OPENAI_API_KEY=sk-your-key-here

# If using HuggingFace (current default)
export OPENAI_API_KEY=hf_your-token-here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

## Setup Instructions
1. Clone the repository and navigate to the project root.
2. Create and activate a Python 3.11 virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Set up your `.env` file from the provided `.env.example`.
5. Run the server locally: `python scripts/launcher.py`

## Docker Instructions
```bash
# Build the image
docker build -t clinical-triage-assistant .

# Run the container
docker run -p 8000:8000 --env-file .env clinical-triage-assistant
```

## HF Space Deployment
1. Create a New Space on Hugging Face using the Docker template.
2. Upload the repository contents.
3. Add `HF_TOKEN`, `MODEL_NAME`, and `API_BASE_URL` to Space Secrets.
4. The environment will automatically start via the Dockerfile CMD.

## Baseline Scores
| Task | Score | Steps |
| :--- | :--- | :--- |
| task_1 | 0.000 | 0 |
| task_2 | 0.000 | 0 |
| task_3 | 0.000 | 0 |

## Medical Foundation
The environment is built on the **Emergency Severity Index (ESI)**, a five-level emergency department triage algorithm. ESI is a valid, reliable triage tool used worldwide to prioritize patients based on both acuity and resource needs, ensuring that the most critical patients receive care first.
