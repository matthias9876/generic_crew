# Task 02 – Work Log Writer

## Objective
Implement `gat/work_log.py` providing the `append_run()` function for agent work documentation.

## Requirements (from Specification §Agent Work Documentation)
Each agent documents its work in a Markdown file scoped to agent + phase. Each entry must contain:
- Task description
- Who assigned the task
- The agent's reasoning and thoughts
- The result delivered
- Links to any produced files

### Function signature
```python
def append_run(
    log_dir: str,
    phase: str,
    agent_name: str,
    task_description: str,
    assigned_by: str,
    thoughts: str,
    result: str,
    produced_files: list[str] | None = None,
) -> str:
```

### Behaviour
- Log file path: `{log_dir}/{phase}/{agent_name}.md`
- Create directories and file if they don't exist.
- If the agent is called multiple times, **append** (not overwrite).
- Each entry has a UTC ISO-8601 timestamp heading.
- Return the absolute path to the log file.

## Acceptance Criteria
- `tests/test_work_log.py` passes.
- Remove the broken `gat/utils/work_log.py` stub (duplicates this module).
