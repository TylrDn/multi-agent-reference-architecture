---
name: add-langfuse-tracing
description: Invoke this agent when Langfuse tracing is absent from core/orchestrator.py or core/executor.py LLM calls — specifically when CallbackHandler is not being passed to ChatOpenAI instances constructed in the core orchestration and execution layers.
model: inherit
readonly: false
---

# Add Langfuse Tracing to multi-agent-reference-architecture

## Objective

Instrument every LLM call in `core/orchestrator.py`, `core/executor.py`, `core/planner.py`, `core/reviewer.py`, and example scripts with Langfuse tracing via `langfuse.callback.CallbackHandler`. Create a centralized observability module at `core/observability.py` as the single source of truth for handler creation. When complete, every language model call emits traces to Langfuse, and the YAML-driven graph assembly pipeline is fully observable.

## Context

This repo uses `langchain_openai.ChatOpenAI` pointed at NIM endpoints. The `core/` layer constructs LLM instances and invokes them in the Planner→Executor→Reviewer loop. Currently, no `CallbackHandler` is attached. Since this is the ISV reference architecture, Langfuse tracing is a required capability that ISV partners expect to configure via environment variables.

## Files to Create/Touch

**Create:**
1. `core/observability.py` — Centralized handler factory.

**Modify:**
2. `core/orchestrator.py` — Import and apply `get_callbacks()`.
3. `core/executor.py` — Import and apply `get_callbacks()`.
4. `core/planner.py` — Import and apply `get_callbacks()`.
5. `core/reviewer.py` — Import and apply `get_callbacks()` if LLM calls are present.
6. `examples/run_sales_pipeline.py` — Ensure tracing is active when example scripts run.
7. `examples/run_support_triage.py` — Same.
8. `examples/run_data_analyst.py` — Same.
9. `.env.template` — Add Langfuse environment variables.
10. `requirements.txt` — Add `langfuse>=2.0.0`.
11. `tests/conftest.py` — Add `mock_langfuse` and `mock_observability` fixtures.

## Step-by-Step Instructions

### Step 1 — Create `core/observability.py`

```python
"""Observability utilities for multi-agent-reference-architecture.

Provides a centralized Langfuse CallbackHandler factory used across
all core orchestration modules. Import from here — never duplicate
handler construction logic in individual files.
"""

import logging
import os

from langfuse.callback import CallbackHandler

logger = logging.getLogger(__name__)


def get_langfuse_handler() -> CallbackHandler:
    """Return a configured Langfuse CallbackHandler.

    Reads credentials from environment:
        LANGFUSE_PUBLIC_KEY: Public key for Langfuse project.
        LANGFUSE_SECRET_KEY: Secret key for Langfuse project.
        LANGFUSE_HOST: Langfuse server URL.
            Defaults to "https://cloud.langfuse.com".

    Returns:
        CallbackHandler: Configured handler. Operates in no-op mode
            (logs a warning) if credentials are not set.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.warning(
            "Langfuse credentials not configured "
            "(LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY missing). "
            "Tracing will be disabled."
        )

    return CallbackHandler(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )


def get_callbacks() -> list[CallbackHandler]:
    """Return the list of active callback handlers for LangChain invocations.

    Used as: `ChatOpenAI(callbacks=get_callbacks())` or
             `await llm.ainvoke(input, config={"callbacks": get_callbacks()})`.

    Returns:
        list[CallbackHandler]: List containing the Langfuse handler.
    """
    return [get_langfuse_handler()]
```

### Step 2 — Read Each Core File

Before modifying, read `core/orchestrator.py`, `core/executor.py`, `core/planner.py`, `core/reviewer.py` to understand:
- Where `ChatOpenAI` is constructed (class `__init__`? module level? per-node function?)
- Whether the LLM instance is shared or created per invocation
- How the YAML agent config is passed through to the LLM

### Step 3 — Update `core/orchestrator.py`

Add import at top:
```python
from core.observability import get_callbacks
```

Find the LLM construction pattern. Update all `ChatOpenAI` instantiations:
```python
# Before:
self.llm = ChatOpenAI(
    model=agent_config.model,
    base_url=os.environ["NIM_BASE_URL"],
    api_key=os.environ["NIM_API_KEY"],
    temperature=0,
)

# After:
self.llm = ChatOpenAI(
    model=agent_config.model,
    base_url=os.environ["NIM_BASE_URL"],
    api_key=os.environ["NIM_API_KEY"],
    temperature=0,
    callbacks=get_callbacks(),
)
```

If orchestrator invokes `self.llm.ainvoke()` or chains, also add:
```python
result = await self.llm.ainvoke(
    messages,
    config={"callbacks": get_callbacks()},
)
```

### Step 4 — Update `core/executor.py`

Same pattern as orchestrator. The executor typically invokes tools and then calls an LLM to process results. Apply `callbacks=get_callbacks()` to the `ChatOpenAI` constructor and `config={"callbacks": get_callbacks()}` to all `ainvoke()` calls.

### Step 5 — Update `core/planner.py`

The planner typically calls an LLM to generate a task plan from the user input and agent state. Same pattern:
```python
from core.observability import get_callbacks

# In planner node function:
async def plan_task(state: AgentState) -> dict:
    langfuse_handler = get_callbacks()
    result = await llm.ainvoke(
        state["messages"],
        config={"callbacks": langfuse_handler},
    )
    return {"plan": result.content}
```

### Step 6 — Update `core/reviewer.py`

If `reviewer.py` calls an LLM to evaluate output quality, apply the same handler injection.

If reviewer logic is purely rule-based (no LLM call), no change is needed — but document this in a comment.

### Step 7 — Update Example Scripts

For `examples/run_sales_pipeline.py`, `examples/run_support_triage.py`, `examples/run_data_analyst.py`:

Add at the top of each file (after imports, before graph construction):
```python
from dotenv import load_dotenv
load_dotenv()

# Langfuse tracing is configured via environment variables.
# Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST in .env.
# Tracing is automatically applied via core/observability.py when
# the orchestrator constructs LLM instances.
```

Confirm `load_dotenv()` is called before any env var reads.

### Step 8 — Update `.env.template`

Add:
```bash
# Langfuse Observability (https://langfuse.com)
# Get keys from: https://cloud.langfuse.com/settings
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Step 9 — Update `requirements.txt`

Add:
```
langfuse>=2.0.0
```

### Step 10 — Update `tests/conftest.py`

```python
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=False)
def mock_langfuse():
    """Patch Langfuse CallbackHandler to prevent network calls in unit tests.

    Use on any test that triggers LLM construction in core/ modules.
    """
    with patch("langfuse.callback.CallbackHandler") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=False)
def mock_observability(mocker):
    """Patch core.observability.get_callbacks to return empty list in unit tests.

    Prevents Langfuse network calls and simplifies LLM mock setup.
    """
    return mocker.patch("core.observability.get_callbacks", return_value=[])
```

Apply `mock_observability` to all unit tests that exercise `core/orchestrator.py`, `core/executor.py`, `core/planner.py`, or `core/reviewer.py`.

## Acceptance Criteria

- [ ] `core/observability.py` exists with `get_langfuse_handler()` and `get_callbacks()` functions, both typed and docstringed.
- [ ] All `ChatOpenAI(...)` constructions in `core/` include `callbacks=get_callbacks()`.
- [ ] All `llm.ainvoke()` and `chain.ainvoke()` calls in `core/` include `config={"callbacks": get_callbacks()}`.
- [ ] `get_callbacks` is imported from `core.observability` — not duplicated in individual files.
- [ ] `.env.template` contains `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.
- [ ] `langfuse>=2.0.0` is in `requirements.txt`.
- [ ] `tests/conftest.py` has `mock_langfuse` and `mock_observability` fixtures.
- [ ] `pytest tests/ -m "not integration"` passes with no new failures.
- [ ] `ruff check . --fix && mypy .` pass clean.
- [ ] All three example scripts load `.env` before graph construction.
- [ ] Running `grep -rn "ChatOpenAI(" core/ --include="*.py"` shows every instance has `callbacks=`.
