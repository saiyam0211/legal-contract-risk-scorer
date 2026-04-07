"""Task configurations for the three difficulty levels."""

from dataclasses import dataclass, field
from typing import List

from environment.contract_data import (
    TASK1_CLAUSES,
    TASK2_CLAUSES,
    TASK2_MISSING_PROTECTIONS,
    TASK3_CLAUSES,
    TASK3_MISSING_PROTECTIONS,
)


@dataclass
class TaskConfig:
    task_id: str
    difficulty: str          # easy | medium | hard
    name: str
    description: str
    clause_ids: List[str]
    max_steps: int
    available_actions: List[str]
    expected_missing_protections: List[str] = field(default_factory=list)


TASKS: dict = {
    "easy_clause_risk": TaskConfig(
        task_id="easy_clause_risk",
        difficulty="easy",
        name="Single Clause Risk Identification",
        description=(
            "You are a legal analyst reviewing 5 individual contract clauses. "
            "For each clause, call 'assess_clause' with the clause_id, risk_level "
            "(low/medium/high/critical), and category "
            "(liability/indemnification/IP/confidentiality/payment/termination/"
            "warranty/governing_law/SLA/data_privacy/other). "
            "When all clauses are reviewed, call 'submit_report' to finish."
        ),
        clause_ids=[c["clause_id"] for c in TASK1_CLAUSES],
        max_steps=6,
        available_actions=["assess_clause", "submit_report"],
        expected_missing_protections=[],
    ),

    "medium_section_analysis": TaskConfig(
        task_id="medium_section_analysis",
        difficulty="medium",
        name="Contract Section Analysis",
        description=(
            "You are reviewing a 12-clause software development contract. "
            "For each clause, call 'assess_clause' with clause_id, risk_level, "
            "category, and is_risky (true/false). "
            "Additionally, call 'flag_missing' with a list of missing standard "
            "protections you identify (e.g. force_majeure, dispute_resolution). "
            "When finished, call 'submit_report'."
        ),
        clause_ids=[c["clause_id"] for c in TASK2_CLAUSES],
        max_steps=15,
        available_actions=["assess_clause", "flag_missing", "submit_report"],
        expected_missing_protections=TASK2_MISSING_PROTECTIONS,
    ),

    "hard_full_review": TaskConfig(
        task_id="hard_full_review",
        difficulty="hard",
        name="Full Contract Risk Report",
        description=(
            "You are performing a full risk review of a 20-clause service agreement. "
            "For each clause, call 'assess_clause' with clause_id, risk_level, "
            "category, is_risky, and reasoning. "
            "Call 'flag_missing' for any missing standard protections "
            "(limitation_of_liability, IP_ownership, confidentiality, "
            "dispute_resolution, force_majeure). "
            "For the 3 highest-risk clauses, call 'suggest_rewrite' with clause_id "
            "and suggested_rewrite containing improved clause text. "
            "When complete, call 'submit_report'."
        ),
        clause_ids=[c["clause_id"] for c in TASK3_CLAUSES],
        max_steps=30,
        available_actions=[
            "assess_clause",
            "flag_missing",
            "suggest_rewrite",
            "submit_report",
        ],
        expected_missing_protections=TASK3_MISSING_PROTECTIONS,
    ),
}

TASK_IDS = list(TASKS.keys())
