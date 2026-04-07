# triage_env/app/api/main.py
from fastapi import FastAPI
from app.api.routes import router
from app.utils.logging import setup_logging, get_logger

# Configure global structured logging at startup
setup_logging()
logger = get_logger("ClinicalTriage")

app = FastAPI(
    title="Clinical Triage Assistant",
    version="1.0.0",
    description="OpenEnv RL environment for emergency room triage"
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initializes and logs state at the start of the simulation lifecycle."""
    logger.info("Clinical Triage Environment service started.")
