"""Executor node — runs tool calls for each task in state['tasks'].

Responsibility
--------------
Iterates over the task list, dispatches each task to the correct tool node
via the tool registry, and accumulates structured results into state['results'].
Partial failures are captured per-task (success=False) without halting the run.
"""
from __future__ import annotations
import logging
from tools.registry import get_tool
from state.schema import AgentState

logger = logging.getLogger(__name__)


def executor_node(state: AgentState) -> dict:
    """Execute all tasks in state['tasks'] and collect results.

    Parameters
    ----------
    state : AgentState
        Must contain 'tasks' list from Planner output.

    Returns
    -------
    dict
        State patch: {"results": list[dict]}

    TODO
    ----
    - Support async parallel execution for independent tasks
    - Bind Langfuse span per tool call with latency + token tracking
    - Implement per-task timeout with configurable deadline
    - Add tool call history to state.messages for LLM context window
    """
    results = []
    for task in state["tasks"]:
        task_id = task.get("id", "unknown")
        tool_name = task.get("tool", "")
        params = task.get("params", {})
        logger.info(f"executor: running task_id='{task_id}' tool='{tool_name}'")

        try:
            tool_fn = get_tool(tool_name)
            output = tool_fn(**params)
            results.append({"task_id": task_id, "output": output, "success": True, "error": None})
        except Exception as exc:
            logger.warning(f"executor: task_id='{task_id}' failed — {exc}")
            results.append({"task_id": task_id, "output": None, "success": False, "error": str(exc)})

    logger.info(f"executor: {sum(r['success'] for r in results)}/{len(results)} tasks succeeded")
    return {"results": results}
