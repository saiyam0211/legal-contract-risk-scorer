"""Deterministic graders for each task.

All graders accept the session state dict and return a float in [0.0, 1.0].
No randomness — identical inputs always produce identical scores.
"""

from typing import Any, Dict, List

from environment.contract_data import ALL_CLAUSES_BY_ID
from environment.models import RISK_ORDER


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _risk_adjacent(predicted: str, ground_truth: str) -> bool:
    """Return True when risk levels are exactly one step apart."""
    p = RISK_ORDER.get(predicted, -1)
    g = RISK_ORDER.get(ground_truth, -1)
    return abs(p - g) == 1


def _keyword_match_ratio(text: str, keywords: List[str]) -> float:
    """Fraction of keywords that appear (case-insensitive) in text."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    matched = sum(1 for kw in keywords if kw.lower() in text_lower)
    return matched / len(keywords)


# ---------------------------------------------------------------------------
# Task 1 grader  (easy)
# ---------------------------------------------------------------------------

def grade_easy_clause_risk(session: Dict[str, Any]) -> float:
    """Score based purely on risk_level accuracy.

    +0.20 for exact match, +0.07 for adjacent level, 0 otherwise.
    Max = 5 × 0.20 = 1.0
    """
    assessments: Dict[str, Dict] = session.get("assessments", {})
    clause_ids: List[str] = session["task_config"].clause_ids

    score = 0.0
    for cid in clause_ids:
        gt = ALL_CLAUSES_BY_ID[cid]
        agent_action = assessments.get(cid, {})
        predicted_risk = agent_action.get("risk_level", "")

        if predicted_risk == gt["risk_level"]:
            score += 0.20
        elif _risk_adjacent(predicted_risk, gt["risk_level"]):
            score += 0.07

    return min(round(score, 4), 1.0)


# ---------------------------------------------------------------------------
# Task 2 grader  (medium)
# ---------------------------------------------------------------------------

def grade_medium_section_analysis(session: Dict[str, Any]) -> float:
    """Weighted score across three dimensions.

    risk_score     = correct_risk_levels / total_clauses       weight 0.40
    category_score = correct_categories  / total_clauses       weight 0.30
    missing_score  = correct_flags / expected_missing_count    weight 0.30
    """
    assessments: Dict[str, Dict] = session.get("assessments", {})
    missing_flagged: List[str] = session.get("missing_flagged", [])
    clause_ids: List[str] = session["task_config"].clause_ids
    expected_missing: List[str] = session["task_config"].expected_missing_protections

    total = len(clause_ids)
    correct_risk = 0
    correct_cat = 0

    for cid in clause_ids:
        gt = ALL_CLAUSES_BY_ID[cid]
        agent_action = assessments.get(cid, {})

        if agent_action.get("risk_level", "") == gt["risk_level"]:
            correct_risk += 1
        elif _risk_adjacent(agent_action.get("risk_level", ""), gt["risk_level"]):
            correct_risk += 0.5  # partial credit for near-miss

        if agent_action.get("category", "") == gt["category"]:
            correct_cat += 1

    risk_score = correct_risk / total if total > 0 else 0.0
    category_score = correct_cat / total if total > 0 else 0.0

    if expected_missing:
        flagged_lower = {f.lower() for f in missing_flagged}
        expected_lower = {e.lower() for e in expected_missing}
        correct_flags = len(flagged_lower & expected_lower)
        missing_score = correct_flags / len(expected_missing)
    else:
        missing_score = 1.0

    final = risk_score * 0.40 + category_score * 0.30 + missing_score * 0.30
    return min(round(final, 4), 1.0)


# ---------------------------------------------------------------------------
# Task 3 grader  (hard)
# ---------------------------------------------------------------------------

def grade_hard_full_review(session: Dict[str, Any]) -> float:
    """Weighted score across three dimensions.

    risk_score    = weighted_risk_correctness / total_clauses   weight 0.35
    missing_score = correct_flags / expected_missing_count      weight 0.30
    rewrite_score = avg keyword_match_ratio for rewrites        weight 0.35
    """
    assessments: Dict[str, Dict] = session.get("assessments", {})
    missing_flagged: List[str] = session.get("missing_flagged", [])
    rewrites: Dict[str, str] = session.get("rewrites", {})
    clause_ids: List[str] = session["task_config"].clause_ids
    expected_missing: List[str] = session["task_config"].expected_missing_protections

    total = len(clause_ids)
    risk_total = 0.0
    for cid in clause_ids:
        gt = ALL_CLAUSES_BY_ID[cid]
        agent_action = assessments.get(cid, {})
        predicted_risk = agent_action.get("risk_level", "")

        if predicted_risk == gt["risk_level"]:
            risk_total += 1.0
        elif _risk_adjacent(predicted_risk, gt["risk_level"]):
            risk_total += 0.4

    risk_score = risk_total / total if total > 0 else 0.0

    # Missing protections
    if expected_missing:
        flagged_lower = {f.lower() for f in missing_flagged}
        expected_lower = {e.lower() for e in expected_missing}
        correct_flags = len(flagged_lower & expected_lower)
        missing_score = correct_flags / len(expected_missing)
    else:
        missing_score = 1.0

    # Rewrite quality: score each rewrite by keyword coverage
    rewrite_ratios: List[float] = []
    for cid, rewrite_text in rewrites.items():
        gt = ALL_CLAUSES_BY_ID.get(cid, {})
        kws = gt.get("rewrite_keywords", [])
        if kws:
            rewrite_ratios.append(_keyword_match_ratio(rewrite_text, kws))
        else:
            # Rewriting a low-risk clause still earns partial credit for effort
            rewrite_ratios.append(0.2)

    rewrite_score = (sum(rewrite_ratios) / len(rewrite_ratios)) if rewrite_ratios else 0.0

    final = risk_score * 0.35 + missing_score * 0.30 + rewrite_score * 0.35
    return min(round(final, 4), 1.0)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

GRADERS = {
    "easy_clause_risk": grade_easy_clause_risk,
    "medium_section_analysis": grade_medium_section_analysis,
    "hard_full_review": grade_hard_full_review,
}


def run_grader(session: Dict[str, Any]) -> float:
    task_id = session["task_id"]
    grader = GRADERS.get(task_id)
    if grader is None:
        return 0.0
    return grader(session)
