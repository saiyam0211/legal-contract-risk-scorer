"""
test_local.py — Complete local test suite for the Legal Contract Risk Scoring environment.

Tests everything the official validators and evaluators will check:
  1. Environment imports and module structure
  2. reset() / step() / state() API
  3. All 3 tasks: full episode with oracle agent (score should be near 1.0)
  4. Grader determinism (same inputs → same score, always)
  5. Reward range (every reward in [0.0, 1.0])
  6. Edge cases: invalid action, repeated clause, submit_report
  7. FastAPI endpoints via TestClient (simulates what validators ping)
  8. openenv.yaml structure check
  9. Dockerfile exists and has required lines
 10. inference.py exists and has required log-format symbols

Run with:
    python test_local.py

All PASS → ready to submit.
"""

import sys
import json
import os

# ── colour helpers ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  {GREEN}PASS{RESET}  {msg}")

def fail(msg, detail=""):
    global failed
    failed += 1
    print(f"  {RED}FAIL{RESET}  {msg}")
    if detail:
        print(f"        {YELLOW}{detail}{RESET}")

def section(title):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─'*55}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Import checks
# ═══════════════════════════════════════════════════════════════════════════
section("1. Module imports")

try:
    from environment.models import (
        ClauseItem, ContractObservation, ContractAction, StepResult,
        RISK_LEVELS, VALID_CATEGORIES,
    )
    ok("environment.models imports cleanly")
except Exception as e:
    fail("environment.models import failed", str(e)); sys.exit(1)

try:
    from environment.contract_data import (
        TASK1_CLAUSES, TASK2_CLAUSES, TASK3_CLAUSES, ALL_CLAUSES_BY_ID,
        TASK2_MISSING_PROTECTIONS, TASK3_MISSING_PROTECTIONS,
    )
    ok("environment.contract_data imports cleanly")
except Exception as e:
    fail("environment.contract_data import failed", str(e)); sys.exit(1)

try:
    from environment.tasks import TASKS, TASK_IDS
    ok("environment.tasks imports cleanly")
except Exception as e:
    fail("environment.tasks import failed", str(e)); sys.exit(1)

try:
    from environment.graders import run_grader, GRADERS
    ok("environment.graders imports cleanly")
except Exception as e:
    fail("environment.graders import failed", str(e)); sys.exit(1)

try:
    import environment.env as env_module
    ok("environment.env imports cleanly")
except Exception as e:
    fail("environment.env import failed", str(e)); sys.exit(1)

try:
    import app as fastapi_app
    ok("app.py (FastAPI) imports cleanly")
except Exception as e:
    fail("app.py import failed", str(e)); sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Data integrity
# ═══════════════════════════════════════════════════════════════════════════
section("2. Contract data integrity")

if len(TASK1_CLAUSES) == 5:
    ok("Task 1 has exactly 5 clauses")
else:
    fail(f"Task 1 clause count wrong", f"expected 5, got {len(TASK1_CLAUSES)}")

if len(TASK2_CLAUSES) == 12:
    ok("Task 2 has exactly 12 clauses")
else:
    fail(f"Task 2 clause count wrong", f"expected 12, got {len(TASK2_CLAUSES)}")

if len(TASK3_CLAUSES) == 20:
    ok("Task 3 has exactly 20 clauses")
else:
    fail(f"Task 3 clause count wrong", f"expected 20, got {len(TASK3_CLAUSES)}")

required_fields = {"clause_id", "text", "risk_level", "category", "is_risky", "rewrite_keywords"}
all_clauses = TASK1_CLAUSES + TASK2_CLAUSES + TASK3_CLAUSES
missing_fields = [
    c["clause_id"] for c in all_clauses
    if not required_fields.issubset(c.keys())
]
if not missing_fields:
    ok("All clauses have required fields")
else:
    fail("Some clauses missing fields", str(missing_fields))

invalid_risks = [c["clause_id"] for c in all_clauses if c["risk_level"] not in RISK_LEVELS]
if not invalid_risks:
    ok("All clauses have valid risk_level")
else:
    fail("Invalid risk_level found", str(invalid_risks))

invalid_cats = [c["clause_id"] for c in all_clauses if c["category"] not in VALID_CATEGORIES]
if not invalid_cats:
    ok("All clauses have valid category")
else:
    fail("Invalid category found", str(invalid_cats))

# Task 2 missing protections
if set(TASK2_MISSING_PROTECTIONS) == {"force_majeure", "dispute_resolution"}:
    ok("Task 2 missing protections correct")
else:
    fail("Task 2 missing protections wrong", str(TASK2_MISSING_PROTECTIONS))

# Task 3 missing protections
expected_t3 = {"limitation_of_liability", "IP_ownership", "dispute_resolution", "force_majeure"}
if set(TASK3_MISSING_PROTECTIONS) == expected_t3:
    ok("Task 3 missing protections correct")
else:
    fail("Task 3 missing protections wrong", str(TASK3_MISSING_PROTECTIONS))


# ═══════════════════════════════════════════════════════════════════════════
# 3. Task configs
# ═══════════════════════════════════════════════════════════════════════════
section("3. Task configurations")

if set(TASK_IDS) == {"easy_clause_risk", "medium_section_analysis", "hard_full_review"}:
    ok("All 3 task IDs present")
else:
    fail("Task IDs wrong", str(TASK_IDS))

for tid, expected_steps in [
    ("easy_clause_risk", 6),
    ("medium_section_analysis", 15),
    ("hard_full_review", 30),
]:
    t = TASKS[tid]
    if t.max_steps == expected_steps:
        ok(f"{tid}: max_steps={expected_steps}")
    else:
        fail(f"{tid}: max_steps wrong", f"expected {expected_steps}, got {t.max_steps}")

# Difficulties
diffs = {tid: TASKS[tid].difficulty for tid in TASK_IDS}
if set(diffs.values()) == {"easy", "medium", "hard"}:
    ok("Tasks cover easy/medium/hard difficulties")
else:
    fail("Difficulty values wrong", str(diffs))


# ═══════════════════════════════════════════════════════════════════════════
# 4. reset() / state() API
# ═══════════════════════════════════════════════════════════════════════════
section("4. reset() / state() API")

for task_id in TASK_IDS:
    result = env_module.reset(task_id)
    sid = result.observation.session_id

    if result.reward == 0.0:
        ok(f"{task_id}: reset() reward=0.0")
    else:
        fail(f"{task_id}: reset() should return reward=0.0", str(result.reward))

    if not result.done:
        ok(f"{task_id}: reset() done=False")
    else:
        fail(f"{task_id}: reset() should return done=False")

    obs = result.observation
    if obs.step == 0:
        ok(f"{task_id}: initial step=0")
    else:
        fail(f"{task_id}: initial step should be 0", str(obs.step))

    if obs.current_clause is not None:
        ok(f"{task_id}: initial current_clause is set")
    else:
        fail(f"{task_id}: initial current_clause is None")

    if len(obs.all_clauses) == len(TASKS[task_id].clause_ids):
        ok(f"{task_id}: all_clauses count matches ({len(obs.all_clauses)})")
    else:
        fail(f"{task_id}: all_clauses count mismatch")

    state = env_module.get_state(sid)
    if state["session_id"] == sid and state["task_id"] == task_id:
        ok(f"{task_id}: state() returns correct session")
    else:
        fail(f"{task_id}: state() session mismatch")


# ═══════════════════════════════════════════════════════════════════════════
# 5. step() — oracle agent (perfect answers)
# ═══════════════════════════════════════════════════════════════════════════
section("5. step() with oracle agent — expect high scores")

def oracle_run(task_id):
    """Run a task with perfect ground-truth answers and return final_score."""
    result = env_module.reset(task_id)
    sid = result.observation.session_id
    task_cfg = TASKS[task_id]
    rewards = []

    # Step 1: assess every clause with exact ground-truth answers
    for cid in task_cfg.clause_ids:
        gt = ALL_CLAUSES_BY_ID[cid]
        action = ContractAction(
            action_type="assess_clause",
            clause_id=cid,
            risk_level=gt["risk_level"],
            category=gt["category"],
            is_risky=gt["is_risky"],
            reasoning="Oracle: exact ground truth.",
        )
        r = env_module.step(sid, action)
        rewards.append(r.reward)
        # Don't return early — let flag_missing / submit_report run first

    # Step 2: flag all missing protections
    if task_cfg.expected_missing_protections:
        action = ContractAction(
            action_type="flag_missing",
            missing_protections=task_cfg.expected_missing_protections,
        )
        r = env_module.step(sid, action)
        rewards.append(r.reward)

    # Step 3: submit to trigger grader
    r = env_module.step(sid, ContractAction(action_type="submit_report"))
    rewards.append(r.reward)
    return r.info.get("final_score", 0.0), rewards

for task_id, min_expected in [
    ("easy_clause_risk", 0.95),
    ("medium_section_analysis", 0.95),   # perfect risk+category+missing flags → ~1.0
    ("hard_full_review", 0.60),          # perfect risk+missing, no rewrites → ~0.65
]:
    score, rewards = oracle_run(task_id)
    if score >= min_expected:
        ok(f"{task_id}: oracle score={score:.3f} >= {min_expected}")
    else:
        fail(f"{task_id}: oracle score too low", f"got {score:.3f}, expected >={min_expected}")

    # Per-step rewards: assess_clause up to 0.30, flag_missing up to 0.50 (5 flags × 0.10)
    bad_rewards = [r for r in rewards if r < -0.1 or r > 0.55]
    if not bad_rewards:
        ok(f"{task_id}: all per-step rewards in valid range")
    else:
        fail(f"{task_id}: out-of-range rewards found", str(bad_rewards))


# ═══════════════════════════════════════════════════════════════════════════
# 6. Grader determinism
# ═══════════════════════════════════════════════════════════════════════════
section("6. Grader determinism")

for task_id in TASK_IDS:
    scores = []
    for _ in range(3):
        s, _ = oracle_run(task_id)
        scores.append(s)
    if len(set(scores)) == 1:
        ok(f"{task_id}: grader is deterministic ({scores[0]:.3f} × 3)")
    else:
        fail(f"{task_id}: grader returned different scores", str(scores))

    # Score must be in [0, 1]
    s = scores[0]
    if 0.0 <= s <= 1.0:
        ok(f"{task_id}: score {s:.3f} in [0.0, 1.0]")
    else:
        fail(f"{task_id}: score out of range", str(s))


# ═══════════════════════════════════════════════════════════════════════════
# 7. Edge cases
# ═══════════════════════════════════════════════════════════════════════════
section("7. Edge cases")

# 7a. Repeated clause assessment → penalty
result = env_module.reset("easy_clause_risk")
sid = result.observation.session_id
cid = TASK1_CLAUSES[0]["clause_id"]
action = ContractAction(action_type="assess_clause", clause_id=cid,
                        risk_level="low", category="confidentiality")
env_module.step(sid, action)  # first time
r2 = env_module.step(sid, action)  # second time — should penalise
if r2.reward < 0:
    ok("Repeated clause assessment returns negative reward (penalty)")
else:
    fail("Repeated clause should penalise", f"got reward={r2.reward}")

# 7b. Invalid action_type → penalty
result = env_module.reset("easy_clause_risk")
sid = result.observation.session_id
r = env_module.step(sid, ContractAction(action_type="fly_to_mars"))
if r.reward < 0:
    ok("Invalid action_type returns negative reward")
else:
    fail("Invalid action_type should penalise", f"got reward={r.reward}")

# 7c. submit_report closes episode
result = env_module.reset("easy_clause_risk")
sid = result.observation.session_id
r = env_module.step(sid, ContractAction(action_type="submit_report"))
if r.done:
    ok("submit_report sets done=True")
else:
    fail("submit_report should set done=True")

# 7d. Stepping after done → still done, reward=0
r2 = env_module.step(sid, ContractAction(
    action_type="assess_clause", clause_id=cid, risk_level="low", category="other"
))
if r2.done and r2.reward == 0.0:
    ok("step() after done returns done=True, reward=0.0")
else:
    fail("step() after done behaved unexpectedly", f"done={r2.done} reward={r2.reward}")

# 7e. Unknown task_id raises ValueError
try:
    env_module.reset("nonexistent_task")
    fail("Unknown task_id should raise ValueError")
except ValueError:
    ok("Unknown task_id raises ValueError")

# 7f. Unknown session_id raises ValueError
try:
    env_module.step("bad-session-id", ContractAction(action_type="submit_report"))
    fail("Unknown session_id should raise ValueError")
except ValueError:
    ok("Unknown session_id raises ValueError")


# ═══════════════════════════════════════════════════════════════════════════
# 8. FastAPI endpoints (TestClient — no server needed)
# ═══════════════════════════════════════════════════════════════════════════
section("8. FastAPI endpoints (TestClient)")

try:
    from fastapi.testclient import TestClient
    client = TestClient(fastapi_app.app)

    # GET /health
    r = client.get("/health")
    if r.status_code == 200 and "status" in r.json():
        ok("GET /health returns 200")
    else:
        fail("GET /health failed", f"status={r.status_code}")

    # POST /reset — default task
    r = client.post("/reset", json={"task_id": "easy_clause_risk"})
    if r.status_code == 200:
        ok("POST /reset returns 200")
    else:
        fail("POST /reset failed", f"status={r.status_code} body={r.text[:200]}")

    data = r.json()
    sid = data["observation"]["session_id"]
    if sid:
        ok("POST /reset returns session_id")
    else:
        fail("POST /reset missing session_id")

    # POST /reset with unknown task → 400
    r = client.post("/reset", json={"task_id": "fake_task"})
    if r.status_code == 400:
        ok("POST /reset with unknown task returns 400")
    else:
        fail("POST /reset with unknown task should return 400", str(r.status_code))

    # POST /step
    step_payload = {
        "session_id": sid,
        "action": {
            "action_type": "assess_clause",
            "clause_id": TASK1_CLAUSES[0]["clause_id"],
            "risk_level": "low",
            "category": "confidentiality",
            "is_risky": False,
        }
    }
    r = client.post("/step", json=step_payload)
    if r.status_code == 200:
        ok("POST /step returns 200")
    else:
        fail("POST /step failed", f"status={r.status_code} body={r.text[:200]}")

    step_data = r.json()
    if "reward" in step_data and "done" in step_data and "observation" in step_data:
        ok("POST /step response has reward, done, observation")
    else:
        fail("POST /step response missing fields", str(list(step_data.keys())))

    # GET /state
    r = client.get(f"/state?session_id={sid}")
    if r.status_code == 200:
        ok("GET /state returns 200")
    else:
        fail("GET /state failed", f"status={r.status_code}")

    # GET /state with unknown session → 404
    r = client.get("/state?session_id=bad-session")
    if r.status_code == 404:
        ok("GET /state with unknown session returns 404")
    else:
        fail("GET /state unknown session should return 404", str(r.status_code))

    # POST /reset with empty body (as validator does with '{}')
    r = client.post("/reset", json={})
    if r.status_code == 200:
        ok("POST /reset with empty body {} returns 200 (uses default task_id)")
    else:
        fail("POST /reset empty body failed", f"status={r.status_code}")

except ImportError:
    fail("fastapi[testclient] not installed — run: pip install httpx")


# ═══════════════════════════════════════════════════════════════════════════
# 9. openenv.yaml structure
# ═══════════════════════════════════════════════════════════════════════════
section("9. openenv.yaml structure")

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print(f"  {YELLOW}SKIP{RESET}  PyYAML not installed — skipping yaml checks (pip install pyyaml)")

if HAS_YAML:
    with open("openenv.yaml") as f:
        spec = yaml.safe_load(f)

    for field in ["name", "version", "description", "tasks", "observation_space", "action_space"]:
        if field in spec:
            ok(f"openenv.yaml has '{field}'")
        else:
            fail(f"openenv.yaml missing '{field}'")

    tasks = spec.get("tasks", [])
    if len(tasks) >= 3:
        ok(f"openenv.yaml defines {len(tasks)} tasks (≥3 required)")
    else:
        fail(f"openenv.yaml needs ≥3 tasks", f"found {len(tasks)}")

    ids = [t.get("id") for t in tasks]
    expected_ids = ["easy_clause_risk", "medium_section_analysis", "hard_full_review"]
    if set(ids) == set(expected_ids):
        ok("All 3 task IDs present in openenv.yaml")
    else:
        fail("Task IDs in yaml don't match", str(ids))

    diffs_in_yaml = [t.get("difficulty") for t in tasks]
    if set(diffs_in_yaml) == {"easy", "medium", "hard"}:
        ok("Difficulties easy/medium/hard all present in yaml")
    else:
        fail("Difficulty values in yaml wrong", str(diffs_in_yaml))


# ═══════════════════════════════════════════════════════════════════════════
# 10. File existence checks
# ═══════════════════════════════════════════════════════════════════════════
section("10. Required file existence")

required_files = [
    "inference.py",
    "openenv.yaml",
    "Dockerfile",
    "requirements.txt",
    "README.md",
    "app.py",
    "environment/__init__.py",
    "environment/models.py",
    "environment/contract_data.py",
    "environment/tasks.py",
    "environment/graders.py",
    "environment/env.py",
]

for f in required_files:
    if os.path.isfile(f):
        ok(f"  {f} exists")
    else:
        fail(f"  {f} MISSING")

# Dockerfile must have EXPOSE 7860
with open("Dockerfile") as f:
    df = f.read()
if "EXPOSE 7860" in df:
    ok("Dockerfile EXPOSEs port 7860")
else:
    fail("Dockerfile must EXPOSE 7860")

if "uvicorn" in df:
    ok("Dockerfile starts uvicorn")
else:
    fail("Dockerfile should start uvicorn")

# inference.py must have the mandatory log symbols
with open("inference.py") as f:
    inf = f.read()
for symbol in ["[START]", "[STEP]", "[END]", "API_BASE_URL", "MODEL_NAME", "HF_TOKEN"]:
    if symbol in inf:
        ok(f"inference.py contains '{symbol}'")
    else:
        fail(f"inference.py missing '{symbol}'")

# requirements.txt must have key packages
with open("requirements.txt") as f:
    reqs = f.read()
for pkg in ["fastapi", "uvicorn", "pydantic", "openai", "httpx"]:
    if pkg in reqs:
        ok(f"requirements.txt includes '{pkg}'")
    else:
        fail(f"requirements.txt missing '{pkg}'")


# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════
total = passed + failed
print(f"\n{BOLD}{'═'*55}{RESET}")
print(f"{BOLD}  Test Summary: {passed}/{total} passed{RESET}")
print(f"{BOLD}{'═'*55}{RESET}")

if failed == 0:
    print(f"\n{GREEN}{BOLD}  All tests passed — ready to submit!{RESET}\n")
    sys.exit(0)
else:
    print(f"\n{RED}{BOLD}  {failed} test(s) failed — fix before submitting.{RESET}\n")
    sys.exit(1)
