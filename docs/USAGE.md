# GAT Usage Guide

## Table of Contents

- [CLI Reference](#cli-reference)
- [Phase 1: Requirements Review](#phase-1-requirements-review)
- [Phase 2: Crew Hiring](#phase-2-crew-hiring)
- [Phase 3: Execution](#phase-3-execution)
- [End-to-End Example](#end-to-end-example)

## CLI Reference

```
python -m gat <subcommand> [options]
```

| Subcommand     | Description                          |
|---------------|--------------------------------------|
| `requirements` | Run the requirements review phase    |
| `hire`         | Generate a crew YAML from requirements |
| `run`          | Execute the crew to fulfil requirements |

### Global Options

| Option     | Default           | Description                    |
|-----------|-------------------|--------------------------------|
| `--models` | `gat/models.yaml` | Path to the model registry YAML |
| `--logs`   | `logs/`           | Root directory for work logs    |

## Phase 1: Requirements Review

```bash
python -m gat requirements --rd <path-to-requirements> [--output review.md] [--models gat/models.yaml] [--logs logs/]
```

**What it does:**
1. Reads the requirements document.
2. A Senior Consultant assesses feasibility and risks.
3. A Requirements Engineer identifies ambiguities and suggests improvements.
4. Writes a review document with three sections.

**Example:**

```bash
python -m gat requirements --rd project/requirements.md --output project/review.md
```

**Output (`review.md`):**

```markdown
# Requirements Review

## Feasibility Assessment
The project is technically feasible but has risks around...

## Clarification Questions & Suggested Improvements
- What is the expected load? ...
```

After reviewing, update your requirements document and re-run if needed.

## Phase 2: Crew Hiring

```bash
python -m gat hire --rd <path-to-requirements> [--output crew.yaml] [--models gat/models.yaml] [--logs logs/]
```

**What it does:**
1. An LLM-driven Hiring Manager reads the requirements.
2. Generates a crew YAML with agents (roles, models, tools) and tasks.
3. Validates the YAML, retries once on failure.
4. Always includes a Technical Author and an integration-test task.

**Example:**

```bash
python -m gat hire --rd project/requirements.md --output project/crew.yaml
```

**Output (`crew.yaml`):**

```yaml
agents:
  - name: Developer
    role: Backend Developer
    goal: Implement the REST API
    backstory: Senior Python developer
    model: dev
    tools: [shell, python_repl]
  - name: Technical Author
    role: Technical Writer
    goal: Write comprehensive documentation
    backstory: Experienced technical writer
    model: large
    tools: []
  - name: Tester
    role: QA Tester
    goal: Validate the implementation
    backstory: QA specialist
    model: tester
    tools: [shell]

tasks:
  - name: implement_api
    description: Build the REST API as specified
    expected_output: Working API code with endpoints
    agent: Developer
  - name: write_documentation
    description: Document the API
    expected_output: Markdown docs in docs/
    agent: Technical Author
  - name: integration_test
    description: Test the full API end-to-end
    expected_output: Test report with pass/fail
    agent: Tester
```

You can manually edit the crew YAML before proceeding to execution.

## Phase 3: Execution

```bash
python -m gat run --rd <path-to-requirements> --crew <path-to-crew-yaml> [--models gat/models.yaml] [--logs logs/]
```

**What it does:**
1. Loads and validates the crew YAML.
2. Creates a shared Python virtual environment.
3. Instantiates agents with LLMs and tools (ShellTool, PythonREPLTool).
4. Prepends the requirements to the first task.
5. Runs all tasks sequentially via CrewAI.
6. Logs each agent's work.

**Example:**

```bash
python -m gat run --rd project/requirements.md --crew project/crew.yaml --logs project/logs/
```

## End-to-End Example

Here's a complete walkthrough building a "URL shortener" project:

```bash
# Step 0: Write requirements
cat > requirements.md << 'EOF'
# URL Shortener

Build a Python CLI tool that:
1. Accepts a long URL and returns a shortened version.
2. Stores mappings in a local SQLite database.
3. Supports a `--resolve` flag to expand a short URL back.
4. Has unit tests with pytest.
EOF

# Step 1: Review requirements
python -m gat requirements --rd requirements.md --output review.md
cat review.md

# Step 2: (Optional) Edit requirements based on review feedback
# vim requirements.md

# Step 3: Hire a crew
python -m gat hire --rd requirements.md --output crew.yaml
cat crew.yaml

# Step 4: (Optional) Edit the crew YAML to adjust agents/tasks
# vim crew.yaml

# Step 5: Execute
python -m gat run --rd requirements.md --crew crew.yaml --logs logs/

# Step 6: Check work logs
find logs/ -name "*.md" -exec echo "---" \; -exec head -5 {} \;
```

### Work Log Structure

After execution, the `logs/` directory will contain:

```
logs/
├── requirements/
│   ├── Senior Consultant.md
│   └── Requirements Engineer.md
├── hiring/
│   └── Hiring Manager.md
├── execution/
│   ├── Developer.md
│   ├── Technical Author.md
│   └── Tester.md
└── venv/             # Shared virtual environment
```
