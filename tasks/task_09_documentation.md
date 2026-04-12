# Task 09 – Technical Documentation

## Objective
Add a **Technical Author** agent to every generated crew that produces comprehensive Markdown documentation for the project.

## Requirements
The Technical Author agent shall:
1. Read the requirements document, the crew YAML, and all task outputs.
2. Produce a `docs/` directory containing:
   - `README.md` — Project overview, installation instructions, quick-start guide.
   - `ARCHITECTURE.md` — System design, module descriptions, data flow.
   - `USAGE.md` — Detailed CLI usage, all subcommands with examples, expected inputs/outputs.
   - `DEVELOPMENT.md` — How to set up a dev environment, run tests, contribute.
3. All documentation must be written in idiomatic Markdown with proper headings, code blocks, and cross-links.

## Agent Definition (for crew YAML)
```yaml
- name: Technical Author
  role: Technical Writer
  goal: >-
    Produce clear, accurate, and complete Markdown documentation
    covering installation, usage, architecture, and development.
  backstory: >-
    An experienced technical writer who turns complex software into
    accessible, well-structured documentation. Values clarity and
    practical examples above all else.
  model: large
  tools: []
```

## Task Definition (for crew YAML)
```yaml
- name: write_documentation
  description: >-
    Read the requirements document, architecture decisions, and all
    task outputs. Produce README.md, ARCHITECTURE.md, USAGE.md, and
    DEVELOPMENT.md in a docs/ directory. Each file must use proper
    Markdown with headings, code fences, and cross-links.
  expected_output: >-
    Four Markdown files in docs/ covering project overview,
    architecture, CLI usage with examples, and developer guide.
  agent: Technical Author
```

## Integration with GAT
- The `hiring_phase.py` prompt must instruct the LLM to **always include a Technical Author** agent and a `write_documentation` task as the second-to-last task (before the integration-test task).
- During the execution phase, the Technical Author task runs after all implementation tasks but before integration testing.

## Acceptance Criteria
- Generated crew YAML includes the Technical Author agent and documentation task.
- Documentation task outputs four `.md` files in `docs/`.
- Each file has a title heading, a table of contents (for files > 3 sections), and at least one code example.
- `tests/test_integration.py` verifies the documentation task is present in every generated crew.
