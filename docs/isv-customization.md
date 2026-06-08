# ISV Customization Guide

This guide is for **partner engineering teams** onboarding the OPER pattern as a blueprint for their own agentic AI product.

## 1. Create a Domain Config

Copy an existing config and edit:

```bash
cp configs/agents/sales_pipeline.yaml configs/agents/my_domain.yaml
```

Key fields to update:

| Field | Description |
|---|---|
| `name` | Unique identifier for your domain |
| `description` | Human-readable summary |
| `model` | NIM model endpoint (see NVIDIA API Catalog) |
| `tools` | List of tools your workflow needs |
| `stages` | Ordered list of task stages with tool bindings |
| `persona` | LLM role, tone, and constraint instructions |

## 2. Register Custom Tools

Add a new file in `tools/` and use the `@register_tool` decorator:

```python
# tools/my_tool.py
from tools.registry import register_tool

@register_tool("my_tool")
def my_tool(param1: str, param2: int) -> dict:
    """What this tool does."""
    # implementation
    return {"result": ...}
```

Then add `import tools.my_tool` to the auto-import block at the bottom of `tools/registry.py`.

## 3. Run Your Domain

```python
from core.graph_builder import build_graph
graph = build_graph("configs/agents/my_domain.yaml")
result = graph.invoke({"goal": "Your domain goal here", ...})
```

## 4. Tune Retry Behaviour

In your YAML config:

```yaml
max_retries: 2        # how many executor retries before forced termination
pass_threshold: 0.75  # minimum reviewer score to accept output
```

## 5. Observability Setup

Set in `.env`:

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

All LLM calls will appear in your Langfuse project dashboard with full input/output traces.

## 6. Deploy

```bash
docker compose up
```

See `deploy/docker-compose.yml` — includes Postgres (for checkpointer) and Redis out of the box.
