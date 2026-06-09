# ISV Customization Guide

This guide is for **partner engineering teams** building custom agentic AI workflows on top of this reference architecture.

## Getting Started

1. Copy `.env.template` to `.env` and set `NVIDIA_API_KEY` (required).
2. Optional: enable **Langfuse tracing** by setting `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and optionally `LANGFUSE_HOST` in `.env`. Tracing degrades gracefully when unset.
3. Install and run from the repo root:

```bash
pip install -r requirements.txt
python -m examples.run_sales_pipeline
```

4. Deploy with root compose (no `cd deploy` required):

```bash
docker compose up --build
```

## Included Example Agents

| Config | Example runner | Purpose |
|---|---|---|
| `configs/agents/sales_pipeline.yaml` | `python -m examples.run_sales_pipeline` | B2B sales pipeline analysis |
| `configs/agents/support_triage.yaml` | `python -m examples.run_support_triage` | Customer support triage |
| `configs/agents/data_analyst.yaml` | `python -m examples.run_data_analyst` | SQL + executive summary analytics |

Each YAML defines `agent.name`, `agent.persona`, `agent.tools`, and `confidence_threshold`. Tools must be registered in `tools/registry.py`.

## Step 1 — Define Your Agent Persona

Create a new YAML file in `configs/agents/`:

```yaml
# configs/agents/my_custom_agent.yaml
agent:
  name: my_custom_agent
  role: My Custom Domain Agent
  persona: >
    You are an expert in your domain. Describe behavior, tone, and focus.
  tools:
    - db_query
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
    return "result"
```

Register it in `tools/registry.py`:

```python
from tools.my_tool import my_custom_tool

_TOOL_MAP: dict[str, BaseTool] = {
    ...
    "my_custom_tool": my_custom_tool,
}
```

Add metadata to `configs/tools.yaml`:

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
curl -X POST http://localhost:8080/run \
  -H 'Content-Type: application/json' \
  -d '{"goal": "Your goal", "config_name": "my_custom_agent"}'
```

## Step 4 — Deploy

```bash
docker compose up --build
```

The API will be available at `http://localhost:8080`.

## Step 5 — Evaluate

Add eval cases to `evals/pipeline_eval.py` and run:

```bash
python -m evals.pipeline_eval
```

## LangSmith (optional)

Enable LangSmith alongside Langfuse:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=multi-agent-reference-architecture
```

Both tracing systems can run concurrently.
