# triage_env/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Optional: Endpoint for LLM inference (e.g., HuggingFace Router)
    API_BASE_URL: str = "https://router.huggingface.co/v1"
    # Optional: Specific LLM model identifier (e.g., meta-llama/Llama-3-70B)
    MODEL_NAME: str = "Qwen/Qwen2.5-72B-Instruct"
    # Optional: Authentication token for Hugging Face Spaces
    HF_TOKEN: str = ""

    # Optional: Toggle for verbose environment debugging
    ENV_DEBUG: bool = False
    # Optional: Maximum allowed steps per simulation episode
    MAX_STEPS: int = 30
    # Optional: Network interface for the FastAPI server to bind to
    APP_HOST: str = "0.0.0.0"
    # Optional: Network port for the FastAPI server
    APP_PORT: int = 8000
    # Optional: Global logging verbosity level (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL: str = "INFO"
    # Optional: Maximum seconds to wait for an LLM response
    INFERENCE_TIMEOUT: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Global settings instance for application-wide configuration
settings = Settings()
