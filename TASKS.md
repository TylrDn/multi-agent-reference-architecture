# TASKS — multi-agent-reference-architecture

**Completion:** 100% (feature-complete; gaps are observability and standards compliance)
**Last Audit:** 2025-01-30
**Repo Role:** NVIDIA SA capstone reference for YAML-driven multi-agent LangGraph systems. Primary ISV customization showcase.

---

## Priority 1 — Critical Gaps (Must Fix)

These gaps violate cross-repo standards or undermine the ISV reference value of this repository.

### 1.1 — Add Langfuse Tracing to core/orchestrator.py and core/executor.py

- [ ] **`core/observability.py`** (create) — Define `get_langfuse_handler()` and `get_callbacks()` as the single source of truth for handler creation in this repo.
  - Acceptance: File exists; both functions are typed and have Google-style docstrings.
- [ ] **`core/orchestrator.py`** — Import `get_callbacks` from `core.observability`; inject `callbacks=get_callbacks()` into every `ChatOpenAI` construction.
  - Acceptance: `grep -n "ChatOpenAI(" core/orchestrator.py` shows `callbacks=` on every match.
- [ ] **`core/executor.py`** — Same as above.
  - Acceptance: Same as above.
- [ ] **`core/planner.py`** — Apply `config={"callbacks": get_callbacks()}` to all `llm.ainvoke()` calls.
  - Acceptance: No LLM invocation in `core/planner.py` lacks a callback config.
- [ ] **`core/reviewer.py`** — Apply handler if LLM calls exist; document with comment if purely rule-based.
  - Acceptance: Either handler is applied or a comment explicitly states no LLM call is made.
- [ ] **`.env.template`** — Add `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.
  - Acceptance: All three variables present in `.env.template` with comments.
- [ ] **`requirements.txt`** — Add `langfuse>=2.0.0`.
  - Acceptance: `python -c "import langfuse"` exits 0 after install.
- [ ] **`tests/conftest.py`** — Add `mock_langfuse` and `mock_observability` fixtures.
  - Acceptance: All existing tests pass after changes; no new network calls in test suite.

> Use the `.cursor/agents/add-langfuse-tracing.md` agent for this task.

---

### 1.2 — Add Root-Level docker-compose.yml

- [ ] **`docker-compose.yml`** (create at repo root) — Developer convenience compose using `env_file: .env`, build context `.`, `deploy/Dockerfile`.
  - Acceptance: `docker compose config` exits 0; `docker compose up` starts API on port 8000.
- [ ] **`README.md`** — Update quick start to use `docker compose up` from root.
  - Acceptance: No instruction to `cd deploy/` in README quick start section.

---

### 1.3 — Verify ISV Customization Doc Accuracy

This repo is feature-complete at 100%, but `docs/isv-customization.md` must perfectly reflect the current YAML-driven architecture. Any documentation inaccuracy directly degrades the ISV experience.

- [ ] **`docs/isv-customization.md`** — Read the doc in full. Verify all code examples match the actual current codebase. Fix any discrepancies.
  - Acceptance: Every code snippet in `isv-customization.md` runs without modification against the current codebase.
- [ ] **`docs/isv-customization.md`** — Confirm all three example agents (`sales_pipeline`, `support_triage`, `data_analyst`) are documented.
  - Acceptance: Each agent has a section with config path, example runner, and customization table.
- [ ] **`docs/isv-customization.md`** — Add Langfuse tracing setup instructions to the "Getting Started" section.
  - Acceptance: Doc explains how to set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` in `.env` to enable tracing.

---

## Priority 2 — Polish (Should Fix)

### 2.1 — YAML Config Validation on Startup

- [ ] **`core/graph_builder.py`** or **`core/config_loader.py`** — Add explicit validation of all required YAML fields (`name`, `model`, `system_prompt`, `tools`, `max_iterations`, `nodes`, `edges`) at config load time. Raise `ValueError` with field name if missing.
  - Acceptance: Loading a malformed YAML config raises `ValueError("<field_name> is required")` before any graph is built.

### 2.2 — Tool Registry Validation at Graph Build Time

- [ ] **`core/graph_builder.py`** — When assembling a graph from a YAML config, validate that every tool name in `config.tools` is present in `tools/registry.py`. Raise `KeyError` with the tool name if not found.
  - Acceptance: Attempting to build a graph with an unregistered tool raises `KeyError("tool_name not found in registry")`.

### 2.3 — CI Coverage Gate

- [ ] **`.github/workflows/ci.yml`** — Add `--cov-fail-under=80` to pytest command.
  - Acceptance: CI fails if coverage for `core/`, `tools/`, `state/` drops below 80%.

### 2.4 — State Checkpointer Tests

- [ ] **`tests/test_checkpointer.py`** (create or expand) — Add tests for `state/checkpointer.py`: verify state is persisted and recovered correctly.
  - Acceptance: Checkpointer tests exist and pass with mocked persistence layer.

### 2.5 — Example Script Error Handling

- [ ] **`examples/run_sales_pipeline.py`**, **`examples/run_support_triage.py`**, **`examples/run_data_analyst.py`** — Add try/except around `graph.ainvoke()` to catch and log graph errors gracefully. Print a user-friendly error message instead of a traceback.
  - Acceptance: Running an example with a missing NIM API key prints a clear error, not a raw Python traceback.

### 2.6 — Add `.dockerignore` at Repo Root

- [ ] **`.dockerignore`** (create) — Exclude `.git`, `.env`, `*.pyc`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `docs/`, `notebooks/`, `tests/`, `evals/`.
  - Acceptance: Docker build context size is reduced; `.env` is not included in the image.

---

## Priority 3 — Enhancements (Nice to Have)

### 3.1 — Add a New Agent Config: Financial Advisor or HR Onboarding

- [ ] **`configs/agents/<new_agent>.yaml`** (create) — Add a fourth agent config demonstrating a new industry vertical.
  - Acceptance: YAML is valid, all tools registered, `build_graph()` compiles, example runner created, `isv-customization.md` updated.

> Use the `.cursor/agents/add-new-agent-config.md` agent for this task.

### 3.2 — Graph Visualization Utility

- [ ] **`core/graph_builder.py`** or a new **`tools/graph_viz.py`** — Add a `visualize_graph(graph, output_path: str) -> None` utility that saves a PNG of the compiled graph using `langgraph.utils.draw_mermaid_png` or similar.
  - Acceptance: `python -c "from tools.graph_viz import visualize_graph; ..."` produces a PNG without crashing.

### 3.3 — Streaming Response Support

- [ ] **`api/server.py`** — Add a `POST /run/stream` endpoint that streams graph output tokens using `graph.astream()` and Server-Sent Events.
  - Acceptance: `curl -N http://localhost:8000/run/stream -d '{"question": "..."}' ` streams tokens as SSE events.

### 3.4 — LangSmith Integration Documentation

- [ ] **`docs/isv-customization.md`** — Add a section on enabling LangSmith tracing via `LANGCHAIN_TRACING_V2=true` as a complement to Langfuse.
  - Acceptance: Section explains the env vars needed and that both systems can run concurrently.

### 3.5 — Add `configs/tools.yaml` Validation

- [ ] **`configs/tools.yaml`** — Confirm all tools listed in `configs/tools.yaml` are implemented and registered in `tools/registry.py`. Add a startup validation step.
  - Acceptance: `python -c "from core.config_loader import validate_tools_config; validate_tools_config()"` exits 0.

---

## Cross-Repo Tasks

These tasks apply identically across `nvidia-nim-agent-toolkit`, `enterprise-rag-pipeline`, and `multi-agent-reference-architecture`.

- [ ] **All repos** — Confirm `langfuse>=2.0.0` is in each repo's `requirements.txt`.
- [ ] **All repos** — Confirm `docker-compose.yml` exists at each repo root.
- [ ] **All repos** — Confirm `.env.template` documents `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.
- [ ] **All repos** — Confirm `ruff check . && mypy .` passes clean in each repo independently.
- [ ] **All repos** — Confirm LangGraph state is `TypedDict` (not `dict`) in every graph file.
- [ ] **All repos** — Confirm no `from langchain.` imports (must be `langchain_core`, `langchain_openai`, or `langchain_community`).
- [ ] **All repos** — Confirm `load_dotenv()` is called before any environment variable reads in every entry point.
