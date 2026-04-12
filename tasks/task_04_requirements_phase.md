# Task 04 – Requirements Phase

## Objective
Implement `gat/phases/requirements_phase.py` — the first of GAT's three sequential phases.

## Requirements (from Specification §Requirements Phase)
GAT starts with a **consultant team**. The team receives a requirements document (RD) whose path is a parameter.

The team shall:
1. Determine whether the requirements are advisable, or flag if the project is a bad idea.
2. Ask for clarification on any unclear requirements.
3. Suggest improvements to the requirements where appropriate.

The phase ends with a **review document** written to a new file.

### Implementation details
- Create two CrewAI Agents (Senior Consultant + Requirements Engineer) using `crewai.Agent` with `llm=LLM(model=models["models"]["large"])`.
- Create two Tasks (feasibility review, requirements analysis).
- Run via `crewai.Crew(..., process=Process.sequential)`.
- Write review document (Markdown) with sections: Feasibility Assessment, Clarification Questions, Suggested Improvements.
- Log each agent's work via `work_log.append_run()`.

### Function signature
```python
def run(rd_path: str, models: dict, log_dir: str, output_path: str) -> str:
```
Returns the absolute path to the review document.

## Acceptance Criteria
- Raises `FileNotFoundError` if `rd_path` doesn't exist.
- Uses `crewai.LLM` for model instantiation (not raw strings).
- Review document contains all three sections.
- Work logs are written for both agents.
- `tests/test_requirements_phase.py` passes.
