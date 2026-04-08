# Env_Cravers: Clinical Triage Assistant

Welcome to the **Env_Cravers** project! This repository contains the Clinical Triage Assistant, an OpenEnv-based RL environment for simulating emergency room triage operations.

## Project Structure

- `/triage_env`: Python-based OpenEnv backend server and RL environment files.

## Prerequisites

- **Python** (3.11+)
- **Docker** (optional, for containerized backend)
- **Algorand TestNet Account** (needed for testing the premium on-chain verification features)

## Setup Instructions

### Backend (`triage_env`) Setup

The backend handles the core logic: processing patient vitals, organizing queues based on the Emergency Severity Index (ESI), and interacting with LLMs.

1. Navigate to the backend directory:
   ```bash
   cd triage_env
   ```

2. Create and activate a Python 3.11 virtual environment:
   ```bash
   python -m venv venv
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   **Important Variables:**
   - `OPENAI_API_KEY`: Required for LLM inference (accepts HuggingFace tokens if `API_BASE_URL` is set to HF).
   - *Algorand Credentials*: Required for executing signed transactions in the premium pipeline.

5. Start the backend:
   ```bash
   python scripts/launcher.py
   # Or using Docker:
   # docker build -t clinical-triage-assistant .
   # docker run -p 8000:8000 --env-file .env clinical-triage-assistant
   ```

## Core Features

- **RL Triage Environment**: A dynamic OpenEnv system testing an agent's ability to allocate resources (beds, trauma bays) and process patients.
- **Algorand Premium Pipeline**: Demonstrates secure request handling by logging a SHA256 consent hash as a note in an Algorand TestNet transaction before API execution.
- **AgentGuard Decision Engine**: A deterministic pre-processor ensuring queries are handled appropriately (premium vs. standard) without LLM ambiguity.
- **Terminal Logging**: Real-time observability of triage operations, decision logs, and on-chain verification status directly in the terminal.

## Medical Foundation

The environment is built on the **Emergency Severity Index (ESI)**, a five-level emergency department triage algorithm. ESI is a valid, reliable triage tool used worldwide to prioritize patients based on both acuity and resource needs, ensuring that the most critical patients receive care first.
