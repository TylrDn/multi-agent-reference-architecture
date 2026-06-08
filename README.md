# multi-agent-reference-architecture

[![CI](https://github.com/TylrDn/multi-agent-reference-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/TylrDn/multi-agent-reference-architecture/actions/workflows/ci.yml)

A generalizable **OPER pattern** (Orchestrator → Planner → Executor → Reviewer) reference
architecture for enterprise multi-agent AI systems. Built on **LangGraph** and **NVIDIA NIM** —
designed as a reusable blueprint that ISV partner engineering teams can adapt to any domain
via a single YAML config, with no Python changes required.

## Why OPER?

Most agentic AI POCs are hardcoded to one domain. OPER separates **what to do** (YAML config)
from **how to do it** (graph execution) — so the same orchestration engine runs sales pipelines,
support triage, and data analytics without touching Python.

## Architecture

```
User Goal
    ↓
Orchestrator  (frames intent)
    ↓
Planner       (decomposes into ordered tasks)
    ↓
Executor      (runs tool calls per task)
    ↓
Reviewer      (scores output → terminate or retry)
    ↓
Final Answer
```

See [docs/architecture.md](docs/architecture.md) for the full Mermaid diagram.

## Quickstart

```bash
git clone https://github.com/TylrDn/multi-agent-reference-architecture.git
cd multi-agent-reference-architecture
pip install -r requirements.txt
cp .env.template .env
# Add NVIDIA_API_KEY to .env

python -m examples.run_sales_pipeline
```

## Three Included Domain Configs

| Config | Domain | Description |
|---|---|---|
| `sales_pipeline.yaml` | B2B Sales | 8-stage qualification → close pipeline |
| `support_triage.yaml` | Customer Support | Severity triage + escalation routing |
| `data_analyst.yaml` | Analytics | SQL → interpret → executive summary |

## Add Your Own Domain (< 30 min)

```yaml
# configs/agents/my_domain.yaml
name: my_domain
model: meta/llama-3.1-70b-instruct
orchestrator:
  persona: "You are an expert in [your domain]..."
reviewer:
  score_threshold: 0.75
  max_retries: 2
tools:
  - name: db_query
  - name: api_get
```

Then: `python -m examples.run_sales_pipeline` (swap config name). No Python changes.

See [docs/isv-customization.md](docs/isv-customization.md) for the full guide.

## API

```bash
uvicorn api.server:app --reload --port 8082

# List available configs
curl http://localhost:8082/configs

# Run an agent
curl -X POST http://localhost:8082/run \
  -H 'Content-Type: application/json' \
  -d '{"goal": "Qualify Acme Corp as an NVIDIA customer", "config_name": "sales_pipeline"}'
```

## Docker

```bash
cd deploy && docker-compose up --build
```

## Key Components

| File | Purpose |
|---|---|
| `core/graph_builder.py` | Assembles LangGraph from YAML config |
| `core/orchestrator.py` | Frames user goal as structured intent |
| `core/planner.py` | Decomposes intent into ordered task list |
| `core/executor.py` | Runs tool calls, falls back to LLM reasoning |
| `core/reviewer.py` | Scores output, routes to retry or terminate |
| `state/schema.py` | TypedDict state shared across all nodes |
| `tools/registry.py` | Dynamic tool loader from YAML |
| `evals/pipeline_eval.py` | LangSmith + keyword eval harness |

## Environment Variables

| Variable | Description |
|---|---|
| `NVIDIA_API_KEY` | NVIDIA NIM API key |
| `NIM_BASE_URL` | NIM endpoint |
| `CHECKPOINT_BACKEND` | `memory` (dev) or `postgres` (prod) |
| `LANGSMITH_API_KEY` | LangSmith tracing |

## Cross-Repo Integration

- [`nvidia-nim-agent-toolkit`](https://github.com/TylrDn/nvidia-nim-agent-toolkit) — NIM-specialized agents plug in as Executor tool nodes
- [`enterprise-rag-pipeline`](https://github.com/TylrDn/enterprise-rag-pipeline) — RAG `/query` endpoint registers as a tool
- [`agentic-guardrails-eval`](https://github.com/TylrDn/agentic-guardrails-eval) — `/run` endpoint is a red-team test target

## Topics

`multi-agent` `langgraph` `reference-architecture` `agent-orchestration` `enterprise-ai` `python` `yaml-config` `nvidia-nim` `agentic-patterns` `oper`
