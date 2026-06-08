# ISV Customization Guide

This guide is for **partner engineering teams** building custom agentic AI workflows on top of this reference architecture.

## Step 1 — Define Your Agent Persona

Create a new YAML file in `configs/agents/`:

```yaml
# configs/agents/my_custom_agent.yaml
agent:
  name: my_custom_agent
  role: My Custom Domain Agent
  persona: >
    You are an expert in <your domain>. <describe behavior, tone, focus>.
  tools:
    - db_query        # use existing tools
    - api_post
  confidence_threshold: 0.85
```

## Step 2 — Register Custom Tool Nodes (optional)

Add a new tool in `tools/`:

```python
# tools/my_tool.py
from langchain_core.tools import tool

@tool
def my_custom_tool(input: str) -> str:
    """Describe what this tool does."""
    # your implementation
    return result
```

Register it in `tools/registry.py`:

```python
from tools.my_tool import my_custom_tool

_TOOL_MAP: dict[str, BaseTool] = {
    ...
    "my_custom_tool": my_custom_tool,
}
```

Add it to `configs/tools.yaml`:

```yaml
tools:
  my_custom_tool:
    description: What this tool does
    input_schema:
      input: string
```

## Step 3 — Run Your Agent

```python
from core.graph_builder import GraphBuilder

builder = GraphBuilder(config_name="my_custom_agent")
result = builder.run("Your goal here")
print(result["final_answer"])
```

Or via the API:

```bash
curl -X POST http://localhost:8080/orchestrate \\
  -H 'Content-Type: application/json' \\
  -d '{"goal": "Your goal", "config": "my_custom_agent"}'
```

## Step 4 — Deploy

```bash
cd deploy
docker-compose up --build
```

The API will be available at `http://localhost:8080`.

## Step 5 — Evaluate

Add eval cases to `evals/pipeline_eval.py` and run:

```bash
python -m evals.pipeline_eval
```

This generates `evals/eval_report.json` with pass/fail per test case — useful for partner workshops and compliance reviews.
