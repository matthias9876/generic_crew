# Task 06 – Execution Phase

## Objective
Implement `gat/phases/execution_phase.py` — runs the crew from the hiring phase to fulfil the requirements.

## Requirements (from Specification §Execution Phase)
1. Load and validate the crew YAML using `config_loader`.
2. Create a shared Python virtual environment (`venv`) at `{log_dir}/venv`.
3. Port `ShellTool` and `PythonREPLTool` from `agentic_scanner/agentic_scanner/main.py`:
   - Both tools must operate inside the shared venv (inject `VIRTUAL_ENV` and prepend venv `bin/` to `PATH`).
4. Instantiate CrewAI `Agent` objects with `llm=LLM(model=models["models"][alias])` and tools as specified in crew YAML.
5. Instantiate `Task` objects and wire agent references.
6. Prepend requirements document content to the first task description.
7. Run via `Crew(..., process=Process.sequential).kickoff()`.
8. **Task Modification**: If a task discovers a previous task's output must change:
   - Archive the original task description in the work log.
   - Re-run the earlier task with updated description.
9. Log each agent's work via `work_log.append_run()`.

### Function signature
```python
def run(rd_path: str, crew_yaml_path: str, models: dict, log_dir: str) -> str:
```
Returns the final result string from the crew.

## Acceptance Criteria
- `ShellTool` and `PythonREPLTool` are real, functional `crewai.tools.BaseTool` subclasses.
- All tool calls use the shared venv environment.
- No placeholder code (`CREW_RESULT`, `SHELL_TOOL`, etc.).
- Work logs written for each agent.
- `tests/test_execution_phase.py` passes.
