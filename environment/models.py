from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClauseItem(BaseModel):
    """A single contract clause presented to the agent."""

    clause_id: str
    text: str
    position: int  # 1-based index within the contract


class ContractObservation(BaseModel):
    """Full observation returned after reset() or step()."""

    session_id: str
    task_id: str
    step: int
    max_steps: int
    # The clause the agent should act on next (None when episode is done)
    current_clause: Optional[ClauseItem] = None
    # All clauses in this task — always provided for full context
    all_clauses: List[ClauseItem] = Field(default_factory=list)
    # clause_ids the agent has already assessed
    reviewed_clauses: List[str] = Field(default_factory=list)
    task_description: str
    available_actions: List[str] = Field(default_factory=list)
    # Missing protections the agent has explicitly flagged so far
    missing_protections_flagged: List[str] = Field(default_factory=list)


class ContractAction(BaseModel):
    """Action submitted by the agent each step.

    action_type options:
      - "assess_clause"   : evaluate a single clause
      - "flag_missing"    : report missing standard protections
      - "suggest_rewrite" : propose improved clause text
      - "submit_report"   : finalise the episode
    """

    action_type: str
    # For assess_clause / suggest_rewrite
    clause_id: Optional[str] = None
    # Risk assessment
    risk_level: Optional[str] = None   # low | medium | high | critical
    category: Optional[str] = None     # see VALID_CATEGORIES in contract_data
    is_risky: Optional[bool] = None
    reasoning: Optional[str] = None
    # For flag_missing
    missing_protections: Optional[List[str]] = None
    # For suggest_rewrite
    suggested_rewrite: Optional[str] = None


class StepResult(BaseModel):
    """Returned by step() and reset()."""

    observation: ContractObservation
    reward: float
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Constants shared across modules
# ---------------------------------------------------------------------------

RISK_LEVELS = ["low", "medium", "high", "critical"]

VALID_CATEGORIES = [
    "liability",
    "indemnification",
    "IP",
    "confidentiality",
    "payment",
    "termination",
    "warranty",
    "governing_law",
    "SLA",
    "data_privacy",
    "other",
]

RISK_ORDER = {r: i for i, r in enumerate(RISK_LEVELS)}  # low=0 … critical=3
