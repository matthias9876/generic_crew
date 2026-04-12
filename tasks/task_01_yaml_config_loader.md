# Task 01 – YAML Config Loader

## Objective
Implement `gat/config_loader.py` providing functions to load and validate YAML configuration files.

## Requirements
1. `load_models(path) -> dict` – Load and return the parsed `models.yaml`.
2. `load_crew(path) -> dict` – Load and return a crew YAML file.
3. `validate_crew(data, models) -> None` – Validate a crew dict:
   - Top-level keys `agents` (list) and `tasks` (list) must exist.
   - Each agent must have: `name`, `role`, `goal`, `backstory`, `model`.
   - Each agent `model` alias must exist in `models["models"]`.
   - Each task must have: `name`, `description`, `expected_output`, `agent`.
   - Each task `agent` must reference an existing agent name.
   - Raise `ValueError` with a descriptive message on any violation.
4. Use `yaml.safe_load` (never `yaml.load`).

## Acceptance Criteria
- All functions work as specified.
- `tests/test_config_loader.py` passes.
- No hard-coded paths; all paths are parameters.
