# Task 03 – Models YAML

## Objective
Create/maintain `gat/models.yaml` — the model registry mapping logical aliases to Ollama model strings.

## Requirements (from Specification §Configuration)
- Pre-filled with the models defined in `agentic_scanner/agentic_scanner/main.py`.
- Keys are logical aliases used in crew YAML files.
- Values are Ollama model strings as accepted by `crewai.LLM`.

### Required aliases (from agentic_scanner)
```yaml
models:
  large:  "ollama/qwen3.5:35b-ctx32k"
  dev:    "ollama/qwen3.5:9b-ctx16k"
  tester: "ollama/mistral:ctx16k"
```

## Acceptance Criteria
- File is valid YAML.
- Top-level key `models` exists.
- All three aliases (`large`, `dev`, `tester`) present with non-empty `ollama/` prefixed strings.
- `tests/test_models_yaml.py` passes.
