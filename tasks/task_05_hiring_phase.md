# Task 05 – Hiring Phase

## Objective
Implement `gat/phases/hiring_phase.py` — an LLM-driven agent that generates a crew YAML from a requirements document.

## Requirements (from Specification §Crew Hiring Phase)
An LLM-driven agent analyses the requirements document and generates a crew YAML file that specifies:
- Agents: roles, goals, backstories, model assignments, tools
- Tasks: descriptions, expected outputs, agent assignments

The YAML follows the structure validated by `config_loader.validate_crew()`.
The generated crew must **always include an integration-test task** as the final task.

### Implementation details
- Use `crewai.LLM` to instantiate the model for the Hiring Manager agent.
- Build a prompt that instructs the LLM to output valid YAML with the crew structure.
- Parse the LLM output with `yaml.safe_load`, validate with `config_loader.validate_crew()`.
- Retry once on validation failure.
- Write the validated YAML to `output_yaml_path`.
- Log via `work_log.append_run()`.

### Function signature
```python
def run(rd_path: str, models: dict, log_dir: str, output_yaml_path: str) -> str:
```
Returns the absolute path to the written crew YAML.

## Acceptance Criteria
- Raises `FileNotFoundError` if `rd_path` doesn't exist.
- Uses real `crewai.LLM` + `crewai.Agent`/`Task`/`Crew` (no stub Crew class).
- Output YAML passes `validate_crew()`.
- Work log is written.
- `tests/test_hiring_phase.py` (to be created) passes.
