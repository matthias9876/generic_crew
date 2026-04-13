# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GAT (Generic Agentic Tool) is a YAML-driven framework that orchestrates multi-agent LLM crews to fulfill software projects. Behavior is driven entirely by YAML configuration; the system requires a local [Ollama](https://ollama.ai) instance — no external API keys.

## Commands

**Install (editable):**
```bash
pip install -e .
```

**Run tests:**
```bash
python -m pytest tests/ -v
python -m pytest tests/test_config_loader.py -v    # single file
python -m pytest tests/ --cov=gat --cov-report=term-missing
```

**CLI usage:**
```bash
python -m gat requirements --rd <req.md> --output review.md
python -m gat hire --rd <req.md> --output crew.yaml
python -m gat run --rd <req.md> --crew crew.yaml --logs logs/
```

## Architecture

### Three-Phase Pipeline

```
requirements.md
      │
      ▼
Phase 1 (requirements_phase.py)  →  review.md
      │  Senior Consultant + Requirements Engineer agents
      ▼
Phase 2 (hiring_phase.py)        →  crew.yaml
      │  Hiring Manager agent generates crew spec
      ▼
Phase 3 (execution_phase.py)     →  code + docs
     Iterative loop:
       for each task: Coder → Critic (PASS/REWORK)
       after all tasks: Integration Test (PASS/FAIL → restart)
       finally: Documentation writer
```

Hard limits in `gat.yaml`: `max_coding_critic_cycles: 3`, `max_integration_retries: 2`, `max_total_iterations: 5`.

### Data Flow

1. **`cli.py`** — Parses args, loads `gat.yaml`, resolves model preset, dispatches to phase.
2. **`config_loader.py`** — Merges user config with built-in defaults; `make_llm(preset_data, role)` creates CrewAI LLM objects keyed by *role* (not agent name).
3. **Phase modules** (`phases/`) — Each creates CrewAI agents/tasks, calls `crew.kickoff()`, appends structured entries to work logs via `work_log.append_run(...)`.
4. **Execution tools** — `ShellTool` and `PythonREPLTool` (subclasses of `crewai.tools.BaseTool`) run in a shared virtual environment at `logs/venv/`.

### Model Preset System

`gat.yaml` defines three presets that map roles to Ollama model strings:
- **fast** — 2B/9B models for quick smoke tests
- **gpu** — 7B/9B models fitting in 12 GB VRAM (default)
- **mixed** — 35B for requirements/criticism (CPU+GPU), 14B for coding

Roles: `requirements`, `coder`, `critic`, `tester`, `writer`. A crew YAML references these aliases; `make_llm()` resolves them at runtime.

### Work Log System

`work_log.py` appends append-only Markdown entries to `{log_dir}/{phase}/{agent_name}.md`. Each entry records: timestamp, task, assigned_by, thoughts, result, and produced files. This is the audit trail for every execution.

### Key Files

| File | Purpose |
|------|---------|
| `gat/cli.py` | Entry point; arg parsing and phase dispatch |
| `gat/config_loader.py` | YAML loading, config merging, model resolution |
| `gat/work_log.py` | Append-only Markdown audit log |
| `gat/phases/requirements_phase.py` | Phase 1 agents and tasks |
| `gat/phases/hiring_phase.py` | Phase 2 — generates crew.yaml via LLM |
| `gat/phases/execution_phase.py` | Phase 3 — iterative coding/critic/integration loop |
| `gat/gat.yaml` | Unified config: presets, limits, timeouts |
| `gat/models.yaml` | Legacy model registry (superseded by gat.yaml) |

## Configuration

`gat.yaml` is the single source of truth for presets, per-phase timeouts, iteration limits, and tool timeouts. `models.yaml` is retained for backward compatibility but is no longer the primary config.

### Remote Ollama instances

Define any number of named Ollama endpoints under `ollama_instances`, set `default_instance`, and optionally override per role via `instances` in a preset:

```yaml
ollama_instances:
  local:
    host: localhost
    port: 11434
  workstation:
    host: 10.17.90.127
    port: 8443
    username: admin
    password: "aF7t..."

default_instance: local

presets:
  gpu:
    models:
      coder: "ollama/qwen2.5-coder:7b"
      critic: "ollama/qwen3.5:9b-ctx16k"
    instances:           # optional — overrides default_instance per role
      critic: workstation
```

Credentials are sent as HTTP Basic Auth (`Authorization: Basic <base64>`). Instances without `username`/`password` connect unauthenticated.

## Extending the Framework

- **New phase**: Add a module under `gat/phases/`, wire it into `cli.py`, and add timeout/limit keys to `gat.yaml`.
- **New tool**: Subclass `crewai.tools.BaseTool` in `execution_phase.py` (or a dedicated tools module) and pass it to the relevant agent.
- **New model preset**: Add a new key under `presets` in `gat.yaml` mapping the five role names to Ollama model strings.
