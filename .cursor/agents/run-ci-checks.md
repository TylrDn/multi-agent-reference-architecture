---
name: run-ci-checks
description: Invoke this agent to run the complete local CI check suite — ruff, mypy, and pytest — and fix any failures before pushing, or when the GitHub Actions CI workflow is red and you need to diagnose the root cause and apply fixes.
model: inherit
readonly: false
---

# Run CI Checks — multi-agent-reference-architecture

## Objective

Execute the full local CI pipeline (ruff, mypy, pytest) in the correct order, interpret any failures, apply fixes, and confirm the suite passes clean. This mirrors `.github/workflows/ci.yml`. Special attention must be paid to the YAML-driven graph assembly tests — these are unique to this repo and must validate that every agent config compiles correctly.

## Context

This repo is 100% feature-complete and CI must remain green. Every PR must pass all three CI stages. The YAML-driven architecture introduces a unique test concern: `core/graph_builder.py` must compile a `StateGraph` from every YAML file in `configs/agents/`, and those tests are part of CI.

## Pre-flight Checks

1. Confirm Python 3.11: `python --version`
2. Confirm dependencies are installed: `pip list | grep langgraph`
3. If missing: `pip install -e ".[dev]"` or `pip install -r requirements.txt`
4. Confirm `.env` exists (copy from `.env.template` if not).
5. Confirm all YAML files in `configs/agents/` are syntactically valid:
   ```bash
   python -c "
   import yaml, glob
   for f in glob.glob('configs/agents/*.yaml'):
       yaml.safe_load(open(f))
       print(f'OK: {f}')
   "
   ```

## Step-by-Step Instructions

### Stage 1 — Ruff Lint

```bash
ruff check . --fix
```

After auto-fix, run without `--fix` to confirm zero errors:
```bash
ruff check .
```

**Common failures and fixes:**

| Error | Fix |
|---|---|
| `E501` (line too long) | Manually wrap to ≤100 chars |
| `F401` (unused import) | Remove the import |
| `F811` (redefinition) | Remove the duplicate definition |
| `UP` rules | Auto-fixed by `--fix` |
| `B` (bugbear) rules | Read the specific error — usually a mutable default or bare `except` |

If `ruff check .` exits non-zero after `--fix`, address each remaining error manually.

### Stage 2 — Mypy Type Check

```bash
mypy . --ignore-missing-imports --python-version 3.11
```

**Common failures specific to this repo:**

| Error | Likely cause | Fix |
|---|---|---|
| `error: Missing return type annotation` | Function in `core/` or `tools/` lacks `-> ReturnType` | Add return type |
| `error: "dict[str, Any]" is not assignable to "AgentState"` | Returning wrong type from a node | Fix the return type to match `AgentState` |
| `error: Value of type variable "StateT" cannot be "AgentState"` | LangGraph StateGraph type variance issue | Add `# type: ignore[type-var]` with explanatory comment |
| `error: Module has no attribute "StructuredTool"` | Wrong import path | Use `from langchain.tools import StructuredTool` |
| `error: Cannot find stub for "yaml"` | Missing type stubs | `pip install types-PyYAML` |
| `error: Cannot find stub for "langfuse"` | Langfuse has no stubs | Add `ignore_missing_imports = true` to `[mypy]` in `pyproject.toml` |

Run mypy until zero errors (or only expected `[import-untyped]` notes that are pre-existing).

### Stage 3 — Pytest

#### Unit tests (default — fast, no external deps):
```bash
pytest tests/ -v --cov=. --cov-report=term-missing -m "not integration"
```

#### YAML config tests specifically:
```bash
pytest tests/ -v -k "config" -m "not integration"
```

These tests verify:
1. All YAML files parse without error.
2. All required fields are present.
3. `build_graph()` compiles successfully for each config.
4. All tools referenced in each config are registered.

**Common failures and fixes:**

| Failure | Cause | Fix |
|---|---|---|
| `KeyError: 'tool_name'` in graph build test | Tool referenced in YAML but not in `tools/registry.py` | Register the tool |
| `ValueError: Node 'X' not found` | YAML `nodes:` list references a node name not in `core/` | Fix the node name in YAML or add the node function |
| `RuntimeError: no running event loop` | Async test not decorated | Add `@pytest.mark.asyncio` |
| `ImportError: cannot import name 'get_callbacks'` | `core/observability.py` missing | Run `add-langfuse-tracing` agent first |
| `AssertionError` in tool registration test | New YAML added but tool not registered | Register the tool in `tools/registry.py` |

#### Async tests:
Confirm all async test functions have `@pytest.mark.asyncio`. If `pytest-asyncio` is not installed: `pip install pytest-asyncio`.

Confirm `pyproject.toml` or `pytest.ini` has:
```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
```
or each async test has the decorator.

### Stage 4 — YAML Config Completeness Check

Run this validation script after pytest to confirm every YAML config has a corresponding example:

```bash
python - <<'EOF'
import glob
import os

configs = {
    os.path.splitext(os.path.basename(f))[0]
    for f in glob.glob("configs/agents/*.yaml")
}
examples = {
    f.replace("examples/run_", "").replace(".py", "")
    for f in glob.glob("examples/run_*.py")
}

missing_examples = configs - examples
if missing_examples:
    print(f"WARNING: No example script for agent configs: {missing_examples}")
    print("Run the 'add-new-agent-config' agent to create missing examples.")
else:
    print(f"OK: All {len(configs)} agent configs have corresponding example scripts.")
EOF
```

If any configs are missing examples, this is a Priority 2 issue (not blocking CI, but should be fixed).

### Stage 5 — Report

After all stages pass:

```
CI Check Summary — multi-agent-reference-architecture
======================================================
Ruff:          PASSED (0 errors)
Mypy:          PASSED (0 errors)
Pytest:        PASSED (X tests passed, Y warnings)
Coverage:      Z% overall (core/: A%, tools/: B%, state/: C%)
YAML configs:  N agent configs, all valid, all have examples.

Files modified:
- list any files changed during this run
```

If a stage cannot be made to pass, document clearly:

```
BLOCKED: <test_name>
Reason: <explanation>
Suggested fix: <action>
Impact: <does this block the PR or is it pre-existing?>
```

## Acceptance Criteria

- [ ] `ruff check .` exits with code 0 (zero errors).
- [ ] `mypy . --ignore-missing-imports --python-version 3.11` exits with code 0.
- [ ] `pytest tests/ -v -m "not integration"` exits with code 0.
- [ ] All YAML config files in `configs/agents/` pass `yaml.safe_load()` validation.
- [ ] `build_graph()` compiles successfully for every YAML config in `configs/agents/`.
- [ ] Coverage for `core/`, `tools/`, `state/` is ≥ 80%.
- [ ] Every agent config has a corresponding example runner in `examples/`.
- [ ] A summary of all changes made is provided.
- [ ] No tests are commented out or skipped without documented justification.
