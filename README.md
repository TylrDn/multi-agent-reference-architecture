# multi-agent-reference-architecture

> Generalizable **Orchestrator → Planner → Executor → Reviewer** (OPER) multi-agent pattern using LangGraph. Plug-and-play tool nodes with YAML-configurable agent personas — designed as a reusable blueprint for enterprise ISV agentic AI deployments.

[![CI](https://github.com/TylrDn/multi-agent-reference-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/TylrDn/multi-agent-reference-architecture/actions)

## Overview

This repo implements a **domain-agnostic multi-agent orchestration pattern** that maps any business workflow to four composable roles:

| Role | Responsibility |
|---|---|
| **Orchestrator** | Top-level router — receives user goal, delegates to sub-agents |
| **Planner** | Decomposes goal into ordered task list |
| **Executor** | Runs tool calls per task, returns structured results |
| **Reviewer** | Scores output quality; routes to retry or terminate |

Swap domain configs in `configs/agents/*.yaml` — no Python changes required.

## Quick Start

```bash
cp .env.template .env   # fill in your API keys
pip install -r requirements.txt
python examples/run_sales_pipeline.py
```

Or with Docker:

```bash
docker compose up
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full Mermaid OPER diagram.

## Repo Structure

```
multi-agent-reference-architecture/
├── core/
│   ├── graph_builder.py      # Assembles LangGraph from YAML agent config
│   ├── orchestrator.py       # Top-level router — delegates to sub-agents
│   ├── planner.py            # Breaks goal into ordered task list
│   ├── executor.py           # Runs tool calls per task
│   └── reviewer.py           # Scores output; routes to retry or terminate
├── tools/
│   ├── api_node.py           # Generic REST tool node
│   ├── db_node.py            # SQL query tool node
│   ├── file_node.py          # File I/O tool node
│   └── registry.py           # Dynamic tool loader from YAML config
├── configs/
│   ├── agents/
│   │   ├── sales_pipeline.yaml
│   │   ├── support_triage.yaml
│   │   └── data_analyst.yaml
│   └── tools.yaml
├── state/
│   ├── schema.py             # TypedDict state definitions
│   └── checkpointer.py       # LangGraph memory / persistence
├── examples/
│   ├── run_sales_pipeline.py
│   └── run_support_triage.py
├── evals/
│   └── pipeline_eval.py
├── deploy/
│   ├── docker-compose.yml
│   └── k8s/
├── docs/
│   ├── architecture.md
│   └── isv-customization.md
└── README.md
```

## Cross-Repo Conventions

- **Secrets:** `python-dotenv` + `.env.template` — never commit real values
- **Observability:** Langfuse tracing on all LLM call paths
- **CI/CD:** GitHub Actions — `ruff`, `mypy`, `pytest` on push
- **Containers:** `docker-compose.yml` with health checks
- **State:** LangGraph `TypedDict` state definitions
- **Docs:** `docs/architecture.md` with Mermaid diagram
- **Python:** 3.11+
