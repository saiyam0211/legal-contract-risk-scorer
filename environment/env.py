"""Core environment class for Legal Contract Risk Scoring.

Session state lives in memory as a plain dict — no database required.
A fresh session_id (UUID) is generated on every reset().
"""

import uuid
from typing import Any, Dict, List, Optional

from environment.contract_data import ALL_CLAUSES_BY_ID
from environment.graders import run_grader
from environment.models import (
    ClauseItem,
    ContractAction,
    ContractObservation,
    RISK_ORDER,
    StepResult,
    VALID_CATEGORIES,
)
from environment.tasks import TASKS, TaskConfig

# Module-level session store: session_id -> session_dict
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Per-step reward constants
_REWARD_RISK_EXACT = 0.15
_REWARD_RISK_ADJACENT = 0.05
_REWARD_CATEGORY_EXACT = 0.10
_REWARD_IS_RISKY_CORRECT = 0.05
_REWARD_FLAG_MISSING_CORRECT = 0.10
_REWARD_SUGGEST_REWRITE = 0.05
_PENALTY_REPEAT_REVIEW = -0.02
_PENALTY_INVALID_ACTION = -0.02


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_clauses(clause_ids: List[str]) -> List[ClauseItem]:
    return [
        ClauseItem(
            clause_id=cid,
            text=ALL_CLAUSES_BY_ID[cid]["text"],
            position=i + 1,
        )
        for i, cid in enumerate(clause_ids)
    ]


def _build_observation(session: Dict[str, Any]) -> ContractObservation:
    task_cfg: TaskConfig = session["task_config"]
    clause_list: List[ClauseItem] = session["clauses"]
    reviewed: List[str] = list(session["assessments"].keys())

    # Determine current clause (next unreviewed)
    current_clause: Optional[ClauseItem] = None
    if not session["done"]:
        for cl in clause_list:
            if cl.clause_id not in session["assessments"]:
                current_clause = cl
                break

    return ContractObservation(
        session_id=session["session_id"],
        task_id=session["task_id"],
        step=session["step"],
        max_steps=task_cfg.max_steps,
        current_clause=current_clause,
        all_clauses=clause_list,
        reviewed_clauses=reviewed,
        task_description=task_cfg.description,
        available_actions=task_cfg.available_actions,
        missing_protections_flagged=list(session["missing_flagged"]),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reset(task_id: str, session_id: Optional[str] = None) -> StepResult:
    """Create a fresh episode for the given task_id and return initial obs."""
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Valid: {list(TASKS.keys())}")

    task_cfg = TASKS[task_id]
    sid = session_id or str(uuid.uuid4())

    session: Dict[str, Any] = {
        "session_id": sid,
        "task_id": task_id,
        "task_config": task_cfg,
        "step": 0,
        "clauses": _build_clauses(task_cfg.clause_ids),
        "assessments": {},      # clause_id -> action dict
        "missing_flagged": [],  # list of flagged missing protection strings
        "rewrites": {},         # clause_id -> rewrite text
        "done": False,
        "cumulative_reward": 0.0,
        "final_score": None,
    }
    SESSIONS[sid] = session

    obs = _build_observation(session)
    return StepResult(observation=obs, reward=0.0, done=False, info={"session_id": sid})


def step(session_id: str, action: ContractAction) -> StepResult:
    """Process one agent action and return the next observation + reward."""
    if session_id not in SESSIONS:
        raise ValueError(f"Unknown session_id '{session_id}'. Call reset() first.")

    session = SESSIONS[session_id]

    if session["done"]:
        obs = _build_observation(session)
        return StepResult(
            observation=obs,
            reward=0.0,
            done=True,
            info={"error": "Episode already finished.", "final_score": session.get("final_score", 0.0)},
        )

    session["step"] += 1
    task_cfg: TaskConfig = session["task_config"]
    reward = 0.0
    info: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Dispatch on action_type
    # ------------------------------------------------------------------

    if action.action_type == "assess_clause":
        reward, info = _handle_assess_clause(session, action)

    elif action.action_type == "flag_missing":
        reward, info = _handle_flag_missing(session, action)

    elif action.action_type == "suggest_rewrite":
        reward, info = _handle_suggest_rewrite(session, action)

    elif action.action_type == "submit_report":
        reward, info = _handle_submit_report(session)

    else:
        reward = _PENALTY_INVALID_ACTION
        info["error"] = f"Unknown action_type '{action.action_type}'."

    # ------------------------------------------------------------------
    # Check episode termination conditions
    # ------------------------------------------------------------------

    # Auto-close only on max_steps (agent can still flag_missing / suggest_rewrite
    # after reviewing all clauses before calling submit_report)
    max_steps_reached = session["step"] >= task_cfg.max_steps

    if not session["done"] and max_steps_reached:
        # Auto-close episode and grade
        final_score = run_grader(session)
        session["done"] = True
        session["final_score"] = final_score
        info["final_score"] = final_score
        info["auto_closed"] = True

    session["cumulative_reward"] = round(session["cumulative_reward"] + reward, 4)
    obs = _build_observation(session)

    return StepResult(
        observation=obs,
        reward=round(reward, 4),
        done=session["done"],
        info=info,
    )


def get_state(session_id: str) -> Dict[str, Any]:
    """Return the raw session state for inspection."""
    if session_id not in SESSIONS:
        raise ValueError(f"Unknown session_id '{session_id}'.")
    s = SESSIONS[session_id]
    return {
        "session_id": s["session_id"],
        "task_id": s["task_id"],
        "step": s["step"],
        "max_steps": s["task_config"].max_steps,
        "done": s["done"],
        "cumulative_reward": s["cumulative_reward"],
        "final_score": s["final_score"],
        "reviewed_count": len(s["assessments"]),
        "total_clauses": len(s["clauses"]),
        "missing_flagged": s["missing_flagged"],
        "rewrites_submitted": list(s["rewrites"].keys()),
    }


# ---------------------------------------------------------------------------
# Action handlers (private)
# ---------------------------------------------------------------------------

def _handle_assess_clause(
    session: Dict[str, Any], action: ContractAction
) -> tuple:
    info: Dict[str, Any] = {}
    clause_id = action.clause_id or ""
    task_cfg: TaskConfig = session["task_config"]

    if clause_id not in {c.clause_id for c in session["clauses"]}:
        return _PENALTY_INVALID_ACTION, {"error": f"clause_id '{clause_id}' not in this task."}

    if clause_id in session["assessments"]:
        return _PENALTY_REPEAT_REVIEW, {"error": f"Already assessed '{clause_id}'. Penalty applied."}

    # Record the assessment
    session["assessments"][clause_id] = {
        "risk_level": (action.risk_level or "").lower(),
        "category": action.category or "",
        "is_risky": action.is_risky,
        "reasoning": action.reasoning or "",
    }

    gt = ALL_CLAUSES_BY_ID[clause_id]
    reward = 0.0

    # Risk level scoring
    predicted_risk = (action.risk_level or "").lower()
    if predicted_risk == gt["risk_level"]:
        reward += _REWARD_RISK_EXACT
        info["risk_feedback"] = "exact"
    elif (
        RISK_ORDER.get(predicted_risk, -99) != -99
        and abs(RISK_ORDER.get(predicted_risk, 0) - RISK_ORDER.get(gt["risk_level"], 0)) == 1
    ):
        reward += _REWARD_RISK_ADJACENT
        info["risk_feedback"] = "adjacent"
    else:
        info["risk_feedback"] = "wrong"

    # Category scoring
    predicted_cat = action.category or ""
    if predicted_cat == gt["category"]:
        reward += _REWARD_CATEGORY_EXACT
        info["category_feedback"] = "exact"
    else:
        info["category_feedback"] = "wrong"

    # is_risky scoring (medium & hard tasks only)
    if task_cfg.task_id != "easy_clause_risk" and action.is_risky is not None:
        if action.is_risky == gt["is_risky"]:
            reward += _REWARD_IS_RISKY_CORRECT
            info["is_risky_feedback"] = "correct"
        else:
            info["is_risky_feedback"] = "wrong"

    info["ground_truth_risk"] = gt["risk_level"]  # omitted in production; useful for debugging
    return reward, info


def _handle_flag_missing(
    session: Dict[str, Any], action: ContractAction
) -> tuple:
    protections = action.missing_protections or []
    if not protections:
        return _PENALTY_INVALID_ACTION, {"error": "missing_protections list is empty."}

    expected: List[str] = session["task_config"].expected_missing_protections
    reward = 0.0
    newly_correct = 0

    expected_lower = [e.lower() for e in expected]
    for prot in protections:
        prot_lower = prot.lower().replace(" ", "_")
        if prot_lower in expected_lower and prot_lower not in session["missing_flagged"]:
            session["missing_flagged"].append(prot_lower)
            reward += _REWARD_FLAG_MISSING_CORRECT
            newly_correct += 1

    return reward, {"newly_correct_flags": newly_correct}


def _handle_suggest_rewrite(
    session: Dict[str, Any], action: ContractAction
) -> tuple:
    clause_id = action.clause_id or ""
    if clause_id not in {c.clause_id for c in session["clauses"]}:
        return _PENALTY_INVALID_ACTION, {"error": f"clause_id '{clause_id}' not in this task."}
    if not action.suggested_rewrite or len(action.suggested_rewrite.strip()) < 10:
        return _PENALTY_INVALID_ACTION, {"error": "suggested_rewrite is too short."}

    session["rewrites"][clause_id] = action.suggested_rewrite.strip()
    # Small immediate reward; real score computed by grader at end
    return _REWARD_SUGGEST_REWRITE, {"rewrite_recorded": clause_id}


def _handle_submit_report(session: Dict[str, Any]) -> tuple:
    final_score = run_grader(session)
    session["done"] = True
    session["final_score"] = final_score
    return 0.0, {"final_score": final_score, "submitted": True}
