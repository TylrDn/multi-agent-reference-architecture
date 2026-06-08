# ISV Customization Guide

This guide shows partner engineering teams how to adapt the OPER reference
architecture to a new domain in under 30 minutes.

## Overview

The architecture is fully config-driven. To deploy a new domain agent you need:

1. A new `configs/agents/<domain>.yaml`
2. Optionally, new tool definitions in `configs/tools.yaml`
3. Run the existing graph — no Python changes required

## Step 1: Create Your Agent Config

Copy an existing config as your starting point:

```bash
cp configs/agents/sales_pipeline.yaml configs/agents/my_domain.yaml
```

Update the key fields:

```yaml
name: my_domain
domain: my_domain
description: What this agent does

model:
  name: meta/llama-3.1-70b-instruct  # Or any NIM-hosted model

reviewer:
  score_threshold: 0.80  # Raise for higher-stakes outputs
  max_iterations: 3      # Reduce for latency-sensitive use cases

orchestrator:
  system_prompt: >
    You are the [Domain] Orchestrator. [Role description.]
    [What you identify. How you set strategy.]

planner:
  system_prompt: >
    You are the [Domain] Planner. Break the goal into steps:
    [List your domain-specific steps here]
    Output a JSON array of task strings.

executor:
  system_prompt: >
    You are the [Domain] Executor. [Tools you use. How you behave.]
  tools:
    - web_search          # Keep if useful
    - analytics_db        # Keep if you need data
    - write_workspace_file

reviewer:
  system_prompt: >
    You are the [Domain] Reviewer. Score the output (0.0-1.0).
    Check: [Your domain-specific quality criteria]
    Output JSON: {"score": 0.0, "feedback": ""}
```

## Step 2: Add Custom Tools (Optional)

Add entries to `configs/tools.yaml`:

```yaml
tools:
  - name: crm_api
    type: api
    description: Query the CRM for customer and deal data
    base_url: https://your-crm.example.com/api/v1

  - name: product_db
    type: db
    description: Query the product catalog database
    connection_string: ""  # Set PRODUCT_DB_URL env var
```

For custom tool logic beyond API/DB/file, add a new node in `tools/` following
the `make_api_tool` factory pattern and register it in `tools/registry.py`.

## Step 3: Run Your Agent

```python
from core.graph_builder import build_graph

graph = build_graph("configs/agents/my_domain.yaml")
result = graph.invoke({"goal": "Your domain-specific goal here"})
print(result["final_answer"])
```

Or via the REST API:

```bash
curl -X POST http://localhost:8083/run \\
  -H 'Content-Type: application/json' \\
  -d '{"goal": "Your goal", "config": "configs/agents/my_domain.yaml"}'
```

## Step 4: Tune Performance

| Parameter | Config Key | Effect |
|---|---|---|
| Response quality | `reviewer.score_threshold` | Higher = stricter, more retries |
| Speed | `reviewer.max_iterations` | Lower = faster, less self-correction |
| Model | `model.name` | Swap NIM model without code changes |
| Tools | `executor.tools` | Restrict tool access per domain |

## Deployment

```bash
# Set your NVIDIA API key
export NVIDIA_API_KEY=your_key_here

# Start the API server
uvicorn api.server:app --host 0.0.0.0 --port 8083

# Or via Docker
docker-compose up --build
```

## Example: Healthcare Triage Agent

```yaml
name: healthcare_triage
domain: healthcare
orchestrator:
  system_prompt: >
    You are a Healthcare Triage Orchestrator. Classify the clinical query
    severity (urgent/routine/informational), identify the clinical domain,
    and set the routing strategy. Always flag when human clinical review is needed.
reviewer:
  score_threshold: 0.90  # Higher threshold for clinical outputs
  max_iterations: 2
```

> ⚠️ High-stakes domains (healthcare, legal, finance) should set `score_threshold: 0.90`
> and always include a human-in-the-loop escalation path.
