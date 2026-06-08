---
name: add-new-agent-config
description: Invoke this agent when an ISV or developer needs to add a new agent persona to the multi-agent reference architecture — specifically when a new configs/agents/*.yaml file needs to be created along with its example runner, tests, and documentation updates.
model: inherit
readonly: false
---

# Add New Agent Config — multi-agent-reference-architecture

## Objective

Guide the complete process of adding a new agent persona to the YAML-driven multi-agent reference architecture. This involves: creating the YAML config, verifying required tools are registered, creating the example runner script, writing tests, and updating `docs/isv-customization.md`. When complete, the new agent runs end-to-end via `examples/run_<agent_name>.py` with no Python changes to `core/`.

## Context

The ISV customization contract of this repo is that new agent personas are added **entirely through YAML config files** in `configs/agents/`. The `core/graph_builder.py` reads these files and dynamically wires a LangGraph graph. This agent enforces that contract and ensures all supporting files are created correctly.

## Pre-flight: Gather Requirements

Before creating any files, answer these questions (ask the user or infer from context):

1. **Agent name** (snake_case): e.g., `financial_advisor`, `code_reviewer`, `hr_onboarding`
2. **NIM model**: which model should this agent use? (default: same as `sales_pipeline.yaml`)
3. **System prompt**: what is the agent's persona and primary instruction?
4. **Required tools**: which tools from `tools/registry.py` does this agent need? List them.
5. **Graph topology**: does this agent use the standard Planner→Executor→Reviewer loop, or a custom node sequence?
6. **Max iterations**: how many loop iterations before forcing completion? (default: 5)

If any of these are not provided, use reasonable defaults based on the `sales_pipeline.yaml` as a template.

## Step-by-Step Instructions

### Step 1 — Read Existing Agent Configs as Reference

Read these files in full before creating anything:
- `configs/agents/sales_pipeline.yaml`
- `configs/agents/support_triage.yaml`
- `configs/agents/data_analyst.yaml`

Note the exact YAML schema, field names, and formatting conventions.

Also read:
- `core/graph_builder.py` — to understand exactly how the YAML is parsed and used.
- `tools/registry.py` — to see what tools are available and their registered names.
- `examples/run_sales_pipeline.py` — as the template for the new example script.

### Step 2 — Create `configs/agents/<agent_name>.yaml`

Create `configs/agents/<agent_name>.yaml` following the exact schema used by existing configs:

```yaml
# configs/agents/<agent_name>.yaml
# Agent configuration for <agent_name>.
# Customization: Edit system_prompt, tools, and max_iterations only.
# Node/edge topology changes require a new YAML config, not Python changes.

name: <agent_name>
model: <nim_model_name>
system_prompt: |
  You are a <role description>. Your primary responsibilities are:
  1. <responsibility 1>
  2. <responsibility 2>
  3. <responsibility 3>

  Always respond with structured, factual information. When uncertain, say so.
  Use the available tools to retrieve information before generating a response.

tools:
  - <tool_name_1>
  - <tool_name_2>

max_iterations: 5

nodes:
  - planner
  - executor
  - reviewer

edges:
  - from: planner
    to: executor
  - from: executor
    to: reviewer
  - from: reviewer
    to: planner
    condition: should_continue
  - from: reviewer
    to: END
    condition: is_complete
```

Validate YAML syntax after writing: `python -c "import yaml; yaml.safe_load(open('configs/agents/<agent_name>.yaml'))"`.

### Step 3 — Verify Required Tools Are Registered

For each tool listed in the YAML `tools:` section, verify it is present in `tools/registry.py`:

```python
# In tools/registry.py, each tool should be registered like:
TOOL_REGISTRY: dict[str, StructuredTool] = {
    "query_database": ...,
    "call_api": ...,
    "read_file": ...,
    "write_file": ...,
    # etc.
}
```

If any required tool is **not** registered:
1. Implement the tool function in the appropriate `tools/*.py` file.
2. Define a Pydantic input schema for the tool.
3. Register it in `tools/registry.py`.
4. Add a unit test in `tests/test_tools.py`.

Example tool implementation pattern:
```python
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool


class MyToolInput(BaseModel):
    """Input schema for my_tool."""
    query: str = Field(description="The query to process")
    limit: int = Field(default=10, description="Maximum results to return")


async def my_tool_func(query: str, limit: int = 10) -> str:
    """Execute my_tool logic.

    Args:
        query: The query to process.
        limit: Maximum results to return.

    Returns:
        str: JSON-encoded results.
    """
    # Implementation here
    ...


my_tool = StructuredTool.from_function(
    func=my_tool_func,
    name="my_tool",
    description="Brief description of what this tool does and when to use it.",
    args_schema=MyToolInput,
    coroutine=my_tool_func,
)
```

### Step 4 — Create `examples/run_<agent_name>.py`

Create an example runner based on `examples/run_sales_pipeline.py`:

```python
"""Example runner for the <agent_name> agent.

Usage:
    python examples/run_<agent_name>.py --question "Your question here"
    python examples/run_<agent_name>.py --interactive

Environment variables:
    NIM_BASE_URL, NIM_API_KEY — Required NIM endpoint config.
    LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY — Optional Langfuse tracing.
"""

import argparse
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()  # Must be called before any imports that read env vars.

from core.graph_builder import build_graph
from core.config_loader import load_agent_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run(question: str) -> str:
    """Run the <agent_name> agent on a single question.

    Args:
        question: The user question to process.

    Returns:
        str: The agent's final answer.
    """
    config = load_agent_config("configs/agents/<agent_name>.yaml")
    graph = build_graph(config)

    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": question}],
        "plan": "",
        "tool_results": [],
        "final_answer": "",
        "iteration": 0,
        "error": None,
        "agent_name": config.name,
    })

    return result["final_answer"]


def main() -> None:
    """CLI entry point for the <agent_name> example."""
    parser = argparse.ArgumentParser(description="Run the <agent_name> agent")
    parser.add_argument("--question", type=str, help="Question to ask the agent")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    args = parser.parse_args()

    if args.interactive:
        print("Interactive mode. Type 'quit' to exit.")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() == "quit":
                break
            answer = asyncio.run(run(question))
            print(f"\nAnswer: {answer}")
    elif args.question:
        answer = asyncio.run(run(args.question))
        print(f"Answer: {answer}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

### Step 5 — Write Tests

Add tests in `tests/test_<agent_name>_config.py`:

```python
"""Tests for <agent_name> agent configuration and graph assembly."""

import pytest
import yaml

from core.graph_builder import build_graph
from core.config_loader import load_agent_config


def test_<agent_name>_config_is_valid_yaml():
    """<agent_name>.yaml is valid YAML and loads without error."""
    with open("configs/agents/<agent_name>.yaml") as f:
        config = yaml.safe_load(f)
    assert config is not None


def test_<agent_name>_config_has_required_fields():
    """<agent_name>.yaml contains all required fields."""
    with open("configs/agents/<agent_name>.yaml") as f:
        config = yaml.safe_load(f)

    required_fields = ["name", "model", "system_prompt", "tools", "max_iterations", "nodes", "edges"]
    for field in required_fields:
        assert field in config, f"Required field '{field}' missing from config"


def test_<agent_name>_graph_compiles(mock_observability):
    """build_graph() returns a compiled graph for the <agent_name> config."""
    config = load_agent_config("configs/agents/<agent_name>.yaml")
    graph = build_graph(config)
    assert graph is not None


def test_<agent_name>_tools_are_registered():
    """All tools referenced in <agent_name>.yaml are registered in the tool registry."""
    from tools.registry import TOOL_REGISTRY

    with open("configs/agents/<agent_name>.yaml") as f:
        config = yaml.safe_load(f)

    for tool_name in config["tools"]:
        assert tool_name in TOOL_REGISTRY, (
            f"Tool '{tool_name}' referenced in <agent_name>.yaml "
            f"is not registered in tools/registry.py"
        )
```

### Step 6 — Update `docs/isv-customization.md`

Append a new section documenting the new agent:

```markdown
## Example: <Agent Name>

The `<agent_name>` agent demonstrates [brief description of use case].

**Config file:** `configs/agents/<agent_name>.yaml`
**Example runner:** `examples/run_<agent_name>.py`

### Customization Points

| Field | Current Value | How to Customize |
|---|---|---|
| `model` | `<current_model>` | Replace with any NIM model name |
| `tools` | `[<tool1>, <tool2>]` | Add tools from `tools/registry.py` |
| `max_iterations` | `5` | Increase for complex tasks, decrease for speed |
| `system_prompt` | See YAML | Rewrite for your specific use case |

### Running the Example

```bash
python examples/run_<agent_name>.py --question "Your question here"
```
```

## Acceptance Criteria

- [ ] `configs/agents/<agent_name>.yaml` exists, passes YAML validation, and contains all required fields.
- [ ] All tools in the YAML `tools:` list are registered in `tools/registry.py`.
- [ ] `examples/run_<agent_name>.py` exists and runs without Python errors (mocking the NIM API).
- [ ] `tests/test_<agent_name>_config.py` exists with at least 4 test functions.
- [ ] All new tests pass: `pytest tests/test_<agent_name>_config.py -v`.
- [ ] `docs/isv-customization.md` documents the new agent with config path, example runner, and customization table.
- [ ] `ruff check . --fix && mypy .` pass clean after all new files are added.
- [ ] `core/graph_builder.py` required zero modifications — the new agent works via YAML alone.
