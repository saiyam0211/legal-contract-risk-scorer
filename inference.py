"""Baseline inference script for the Legal Contract Risk Scoring environment.

Usage:
    export HF_TOKEN=<your-token>
    export API_BASE_URL=https://router.huggingface.co/v1   # or your endpoint
    export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
    python inference.py

The script runs all 3 tasks sequentially and emits mandatory log lines:
    [START] task=<task_id> env=legal-contract-risk-scorer model=<model>
    [STEP]  step=<n> action=<str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,...,rn>
"""

import json
import os
import textwrap
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN: str = os.getenv("HF_TOKEN")                    # NO default — must be set
LOCAL_IMAGE_NAME: str = os.getenv("LOCAL_IMAGE_NAME")    # optional, for from_docker_image()

ENV_BASE_URL: str = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK: str = "legal-contract-risk-scorer"
SUCCESS_THRESHOLD: float = 0.30  # score >= threshold → success

TASK_IDS: List[str] = [
    "easy_clause_risk",
    "medium_section_analysis",
    "hard_full_review",
]

MAX_STEPS_PER_TASK: Dict[str, int] = {
    "easy_clause_risk": 6,
    "medium_section_analysis": 15,
    "hard_full_review": 30,
}

TEMPERATURE: float = 0.2
MAX_TOKENS: int = 512

# ---------------------------------------------------------------------------
# Logging helpers (mandatory format)
# ---------------------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    err = error if error else "null"
    done_str = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={err}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# System + user prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""
    You are a senior legal analyst specializing in contract risk assessment.
    You will be shown a list of contract clauses. Your job is to review each
    clause and respond with a JSON action.

    AVAILABLE ACTION TYPES:
      - assess_clause   : evaluate a clause
      - flag_missing    : report missing standard protections
      - suggest_rewrite : propose improved clause text
      - submit_report   : finalize the episode (call only when done)

    RISK LEVELS (use exactly): low, medium, high, critical
    CATEGORIES (use exactly):
      liability, indemnification, IP, confidentiality, payment,
      termination, warranty, governing_law, SLA, data_privacy, other

    Respond with ONLY a valid JSON object — no prose, no markdown:
    {
      "action_type": "assess_clause",
      "clause_id": "t1_c1",
      "risk_level": "high",
      "category": "indemnification",
      "is_risky": true,
      "reasoning": "Unlimited indemnification without cap.",
      "missing_protections": null,
      "suggested_rewrite": null
    }
""").strip()


def _build_user_prompt(obs: Dict[str, Any], step_num: int) -> str:
    task_desc = obs.get("task_description", "")
    reviewed = obs.get("reviewed_clauses", [])
    flagged = obs.get("missing_protections_flagged", [])
    current = obs.get("current_clause")
    available = obs.get("available_actions", [])
    all_clauses = obs.get("all_clauses", [])

    # Build clause list summary
    clause_lines = []
    for cl in all_clauses:
        status = "[REVIEWED]" if cl["clause_id"] in reviewed else "[PENDING]"
        clause_lines.append(f"  {status} [{cl['clause_id']}] (pos {cl['position']})")

    clause_summary = "\n".join(clause_lines) if clause_lines else "  (none)"

    current_text = ""
    if current:
        current_text = (
            f"\nCURRENT CLAUSE TO ASSESS:\n"
            f"  ID   : {current['clause_id']}\n"
            f"  TEXT : {current['text']}"
        )

    return textwrap.dedent(f"""
        STEP: {step_num}
        TASK: {task_desc}

        CLAUSES IN THIS CONTRACT:
        {clause_summary}

        ALREADY REVIEWED: {reviewed}
        MISSING PROTECTIONS FLAGGED SO FAR: {flagged}
        AVAILABLE ACTIONS: {available}
        {current_text}

        Choose your next action and return a single JSON object.
    """).strip()


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_llm(client: OpenAI, obs: Dict[str, Any], step_num: int) -> Dict[str, Any]:
    user_prompt = _build_user_prompt(obs, step_num)
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        # Fallback: assess the current clause as medium risk
        current = obs.get("current_clause") or {}
        return {
            "action_type": "assess_clause",
            "clause_id": current.get("clause_id", ""),
            "risk_level": "medium",
            "category": "other",
            "is_risky": True,
            "reasoning": "Fallback default.",
            "missing_protections": None,
            "suggested_rewrite": None,
        }


# ---------------------------------------------------------------------------
# Environment HTTP helpers
# ---------------------------------------------------------------------------

def env_reset(http: httpx.Client, task_id: str) -> Dict[str, Any]:
    r = http.post("/reset", json={"task_id": task_id}, timeout=30)
    r.raise_for_status()
    return r.json()


def env_step(http: httpx.Client, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"session_id": session_id, "action": action}
    r = http.post("/step", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------

def run_task(task_id: str, client: OpenAI, http: httpx.Client) -> float:
    max_steps = MAX_STEPS_PER_TASK[task_id]
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        result = env_reset(http, task_id)
        obs = result["observation"]
        session_id = obs["session_id"]
        done = result.get("done", False)

        for step_num in range(1, max_steps + 1):
            if done:
                break

            action = call_llm(client, obs, step_num)
            action_str = (
                f"{action.get('action_type','')}:"
                f"{action.get('clause_id','')}"
            )

            result = env_step(http, session_id, action)
            obs = result["observation"]
            reward = float(result.get("reward", 0.0))
            done = result.get("done", False)
            info = result.get("info", {})
            error = info.get("error", None)

            rewards.append(reward)
            steps_taken = step_num
            log_step(step=step_num, action=action_str, reward=reward, done=done, error=error)

            if done:
                score = float(info.get("final_score", 0.0))
                break

        if not done:
            # Force submit
            result = env_step(http, session_id, {"action_type": "submit_report"})
            final_info = result.get("info", {})
            score = float(final_info.get("final_score", 0.0))
            rewards.append(float(result.get("reward", 0.0)))
            steps_taken += 1
            log_step(
                step=steps_taken,
                action="submit_report:",
                reward=float(result.get("reward", 0.0)),
                done=True,
                error=None,
            )

        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_id} error: {exc}", flush=True)
        score = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    with httpx.Client(base_url=ENV_BASE_URL) as http:
        # Quick health check
        try:
            health = http.get("/health", timeout=10)
            health.raise_for_status()
            print(f"[DEBUG] Environment healthy: {health.json()}", flush=True)
        except Exception as exc:
            print(f"[DEBUG] Health check failed: {exc}. Proceeding anyway.", flush=True)

        all_scores: List[float] = []
        for task_id in TASK_IDS:
            task_score = run_task(task_id, client, http)
            all_scores.append(task_score)
            print(f"[DEBUG] {task_id} score = {task_score:.3f}", flush=True)

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"[DEBUG] Overall average score: {overall:.3f}", flush=True)


if __name__ == "__main__":
    main()
