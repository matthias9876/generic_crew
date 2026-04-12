# GAT Development Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Project Layout](#project-layout)
- [Adding a New Phase](#adding-a-new-phase)
- [Adding a New Tool](#adding-a-new-tool)
- [Conventions](#conventions)

## Prerequisites

- Python 3.10+
- Ollama (for live runs; not needed for tests)
- pip

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd generic_crew

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e .
pip install pytest

# Verify
python -m gat --help
```

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_config_loader.py -v

# Run with coverage (requires pytest-cov)
pip install pytest-cov
python3 -m pytest tests/ --cov=gat --cov-report=term-missing
```

All tests mock LLM calls, so no Ollama instance is needed to run them.

## Project Layout

```
gat/
├── cli.py               # CLI entry point & argument parsing
├── config_loader.py     # YAML load/validate (models + crew)
├── work_log.py          # Append-only Markdown work logs
├── models.yaml          # Model alias → Ollama string mapping
└── phases/
    ├── requirements_phase.py   # Phase 1: Consultant team review
    ├── hiring_phase.py         # Phase 2: Generate crew YAML
    └── execution_phase.py      # Phase 3: Run the crew
```

## Adding a New Phase

1. Create `gat/phases/new_phase.py` with a `run(...)` function.
2. Add CLI subcommand in `cli.py`:
   ```python
   new_parser = subparsers.add_parser("newphase", help="Description")
   new_parser.add_argument("--rd", required=True)
   ```
3. Add dispatch in `cli.py`'s `main()`.
4. Write tests in `tests/test_new_phase.py`.
5. Add integration test in `tests/test_integration.py`.

## Adding a New Tool

Tools are `crewai.tools.BaseTool` subclasses. See `execution_phase.py` for the pattern:

```python
from crewai.tools import BaseTool

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "What this tool does."

    def _run(self, input: str) -> str:
        # Tool logic here
        return "result"
```

Register the tool name in the `tool_map` dict in `execution_phase.py`.

## Conventions

- **YAML over code** – Agent definitions, model assignments, and task specs belong in YAML.
- **`yaml.safe_load` only** – Never use `yaml.load`.
- **Work logs** – Every agent must call `work_log.append_run()` after completing work.
- **Test isolation** – All tests mock LLM/CrewAI calls. No network/Ollama required.
- **Model aliases** – Use `large`, `dev`, `tester` in crew YAML. Map to Ollama strings in `models.yaml`.
