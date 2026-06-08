# ISV Customization Guide

This guide explains how partner engineering teams can adapt the OPER reference
architecture to their own domains in under 30 minutes — without modifying core Python.

## What You Need

- An NVIDIA API key (for NIM inference)
- A Python 3.11 environment
- Your domain knowledge translated into a YAML config

## Step 1 — Clone and Install

```bash
git clone https://github.com/TylrDn/multi-agent-reference-architecture.git
cd multi-agent-reference-architecture
pip install -r requirements.txt
cp .env.template .env
# Add your NVIDIA_API_KEY to .env
```

## Step 2 — Create Your Agent Config

Create `configs/agents/my_domain.yaml`:

```yaml
name: my_domain
description: "Brief description of what this agent does."
model: meta/llama-3.1-70b-instruct

orchestrator:
  persona: |
    You are an expert in [your domain]. Your role is to [primary objective].
    When given a goal, you frame it clearly so it can be broken into discrete tasks.

reviewer:
  score_threshold: 0.75   # Raise for higher accuracy; lower for speed
  max_retries: 2

tools:
  - name: db_query          # Use any tool registered in configs/tools.yaml
  - name: api_get
  - name: file_write
```

## Step 3 — Register Custom Tools (Optional)

If you need a tool not in `configs/tools.yaml`:

1. Add a function to `tools/my_tool.py`
2. Register it in `configs/tools.yaml`:
```yaml
my_tool_name:
  module: tools.my_tool
  function: my_function
  description: "What this tool does."
```
3. Reference it in your agent YAML under `tools:`

## Step 4 — Run

```bash
python - <<'EOF'
import uuid
from core.graph_builder import build_graph
from state.schema import AgentState

graph = build_graph("my_domain")
state = {
    "goal": "Your goal here",
    "session_id": str(uuid.uuid4()),
    "config_name": "my_domain",
    "max_retries": 2,
    "messages": [],
    "task_results": [],
    "retry_count": 0,
}
result = graph.invoke(state, config={"configurable": {"thread_id": state["session_id"]}})
print(result["final_answer"])
EOF
```

## Step 5 — Deploy via API

```bash
uvicorn api.server:app --reload --port 8082
# POST /run with {"goal": "...", "config_name": "my_domain"}
```

## Step 6 — Docker

```bash
cd deploy && docker-compose up --build
```

## Tuning the Reviewer

| Parameter | Effect |
|---|---|
| `score_threshold: 0.9` | Very strict — more retries, higher quality |
| `score_threshold: 0.5` | Lenient — faster, may accept partial answers |
| `max_retries: 0` | Single pass — no retry loop |
| `max_retries: 5` | Aggressive retry — for complex multi-step tasks |

## Architecture Reference

See [docs/architecture.md](architecture.md) for the full OPER flow diagram.

## Support

For questions, open an issue or reach out via the NVIDIA Developer Forums.
