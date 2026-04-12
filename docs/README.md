# GAT – Generic Agentic Tool

GAT is a generic, local-LLM-powered agentic tool whose behaviour is driven by YAML configuration files rather than hard-coded logic. It orchestrates AI agent crews through three sequential phases to fulfil arbitrary software projects.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](ARCHITECTURE.md)
- [Development](DEVELOPMENT.md)

## Features

- **YAML-driven configuration** – Agents, models, and tasks are defined in YAML, not code.
- **Three-phase pipeline** – Requirements review → Crew hiring → Execution.
- **Local LLMs** – Runs entirely on local Ollama models (no API keys needed).
- **Automatic work logging** – Every agent documents its reasoning and outputs in Markdown.
- **Shared virtual environment** – All tool calls operate in a single venv for reproducibility.

## Quick Start

```bash
# 1. Install
cd generic_crew
pip install -e .

# 2. Review requirements
python -m gat requirements --rd my_project/requirements.md --output review.md

# 3. Generate a crew
python -m gat hire --rd my_project/requirements.md --output crew.yaml

# 4. Execute the project
python -m gat run --rd my_project/requirements.md --crew crew.yaml
```

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally with the required models:
  - `qwen3.5:35b-ctx32k` (aliased as `large`)
  - `qwen3.5:9b-ctx16k` (aliased as `dev`)
  - `mistral:ctx16k` (aliased as `tester`)
- CrewAI (`pip install crewai`)

### Install GAT

```bash
git clone <repo-url>
cd generic_crew
pip install -e .
```

### Verify installation

```bash
python -m gat --help
python -m pytest tests/ -v
```

## Usage

See [USAGE.md](USAGE.md) for detailed CLI reference and examples.
