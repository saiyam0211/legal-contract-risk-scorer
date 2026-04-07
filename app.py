"""FastAPI server exposing the Legal Contract Risk Scoring environment.

Endpoints:
  POST /reset   — start or restart an episode
  POST /step    — submit an action and get next observation + reward
  GET  /state   — inspect current session state (debugging)
  GET  /health  — liveness probe
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import environment.env as env_module
from environment.models import ContractAction, StepResult
from environment.tasks import TASK_IDS

app = FastAPI(
    title="Legal Contract Risk Scoring",
    description=(
        "OpenEnv-compliant environment where AI agents learn to review "
        "contract clauses, identify risks, and flag missing protections."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response helpers
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "easy_clause_risk"
    session_id: Optional[str] = None


class StepRequest(BaseModel):
    session_id: str
    action: ContractAction


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "tasks": TASK_IDS}


@app.post("/reset", response_model=StepResult)
def reset(request: ResetRequest):
    if request.task_id not in TASK_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{request.task_id}'. Valid: {TASK_IDS}",
        )
    result = env_module.reset(task_id=request.task_id, session_id=request.session_id)
    return result


@app.post("/step", response_model=StepResult)
def step(request: StepRequest):
    try:
        result = env_module.step(session_id=request.session_id, action=request.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result


@app.get("/state")
def state(session_id: str):
    try:
        return env_module.get_state(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
