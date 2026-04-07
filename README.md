---
title: Legal Contract Risk Scorer
emoji: "⚖️"
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Legal Contract Clause Risk Scoring — OpenEnv Environment

An OpenEnv-compliant reinforcement-learning environment where AI agents practice
reviewing legal contracts — identifying risky clauses, categorising provisions,
flagging missing standard protections, and proposing safer rewrites.

Lawyers and legal-ops teams do this work every day. This environment lets you
train and benchmark agents on the same task at three difficulty levels.

---

## Quick Start

### Docker (recommended)

```bash
docker build -t contract-env .
docker run -p 7860:7860 contract-env
```

### Local

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Submit an action |
| `GET` | `/state?session_id=...` | Inspect current session |
| `GET` | `/health` | Liveness probe |

### Reset

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_clause_risk"}'
```

### Step

```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<from reset>",
    "action": {
      "action_type": "assess_clause",
      "clause_id": "t1_c2",
      "risk_level": "critical",
      "category": "indemnification",
      "is_risky": true,
      "reasoning": "Unlimited indemnification with no cap."
    }
  }'
```

---

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique episode identifier |
| `task_id` | string | Which task is active |
| `step` | int | Current step number |
| `max_steps` | int | Episode step limit |
| `current_clause` | object\|null | Clause the agent should act on next |
| `all_clauses` | array | All clauses in this task (for full context) |
| `reviewed_clauses` | array | IDs of already-assessed clauses |
| `task_description` | string | Natural-language task instructions |
| `available_actions` | array | Valid action_type values for this task |
| `missing_protections_flagged` | array | Protections flagged so far |

---

## Action Space

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | string | yes | `assess_clause` / `flag_missing` / `suggest_rewrite` / `submit_report` |
| `clause_id` | string | for assess/rewrite | Target clause |
| `risk_level` | string | for assess | `low` / `medium` / `high` / `critical` |
| `category` | string | for assess | See categories below |
| `is_risky` | bool | medium/hard tasks | Whether the clause poses legal risk |
| `reasoning` | string | optional | Free-text explanation |
| `missing_protections` | array | for flag_missing | List of missing protection names |
| `suggested_rewrite` | string | for suggest_rewrite | Improved clause text |

**Valid categories:** `liability`, `indemnification`, `IP`, `confidentiality`,
`payment`, `termination`, `warranty`, `governing_law`, `SLA`, `data_privacy`, `other`

---

## Tasks

### Task 1 — Single Clause Risk Identification (`easy_clause_risk`)

**Difficulty:** Easy | **Max steps:** 6 | **Clauses:** 5

The agent reviews 5 individual contract clauses in isolation. For each clause it
must call `assess_clause` with the correct `risk_level` and `category`.

**Grader:** +0.20 per exact risk level match, +0.07 for adjacent level.
Maximum score = 1.0.

**Expected baseline score:** ~0.65–0.75

---

### Task 2 — Contract Section Analysis (`medium_section_analysis`)

**Difficulty:** Medium | **Max steps:** 15 | **Clauses:** 12

A 12-clause software development contract. The agent must assess risk level,
category, and `is_risky` for each clause, and also `flag_missing` for any
absent standard protections.

**Grader:** 40% risk level accuracy + 30% category accuracy + 30% missing protections recall.

**Missing protections to find:** `force_majeure`, `dispute_resolution`

**Expected baseline score:** ~0.50–0.60

---

### Task 3 — Full Contract Risk Report (`hard_full_review`)

**Difficulty:** Hard | **Max steps:** 30 | **Clauses:** 20

A complex 20-clause service agreement with subtle risks and 4 missing standard
protections. The agent must assess all clauses, flag all missing protections, and
call `suggest_rewrite` for at least the top risky clauses.

**Grader:** 35% risk level accuracy + 30% missing protections recall + 35% rewrite
quality (keyword coverage).

**Missing protections to find:** `limitation_of_liability`, `IP_ownership`,
`dispute_resolution`, `force_majeure`

**Expected baseline score:** ~0.30–0.45

---

## Reward Function

Rewards are issued at every step (partial credit, not just at episode end):

| Event | Reward |
|-------|--------|
| Exact risk level match | +0.15 |
| Adjacent risk level | +0.05 |
| Exact category match | +0.10 |
| Correct `is_risky` flag | +0.05 |
| Correct missing protection flagged | +0.10 |
| Rewrite submitted | +0.05 |
| Repeated clause assessment | −0.02 |
| Invalid action | −0.02 |

The final episode score (0.0–1.0) is computed by the task grader and returned
in `info.final_score` when `done=True`.

---

## Running the Baseline Inference Script

```bash
export HF_TOKEN=<your-huggingface-token>
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_BASE_URL=http://localhost:7860   # or your HF Space URL

python inference.py
```

The script runs all 3 tasks and prints `[START]`, `[STEP]`, and `[END]` log lines
as required by the OpenEnv evaluation harness.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `HF_TOKEN` | — | HuggingFace / API key |
| `ENV_BASE_URL` | `http://localhost:7860` | Environment server URL |

---

## Project Structure

```
├── app.py                    # FastAPI server
├── inference.py              # Baseline inference script
├── openenv.yaml              # OpenEnv spec
├── Dockerfile
├── requirements.txt
└── environment/
    ├── __init__.py
    ├── models.py             # Pydantic models
    ├── contract_data.py      # Synthetic clauses + ground truth
    ├── tasks.py              # Task configurations
    ├── graders.py            # Deterministic scoring
    └── env.py                # Core environment logic
```

---

## Why This Environment?

- **Commercial value:** Contract review is a $50B/year legal services activity
- **Clear ground truth:** Risk levels and categories are deterministically verifiable
- **Natural difficulty gradient:** 5 → 12 → 20 clauses with increasing subtlety
- **Rich partial rewards:** Every correct assessment earns credit, not just final score
- **Generalisable:** Same format applies to NDAs, employment contracts, SaaS agreements
