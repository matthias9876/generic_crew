# Task 07 – CLI

## Objective
Implement `gat/cli.py` and `gat/__main__.py` — the command-line interface for all three phases.

## Requirements
Three subcommands:
- `python -m gat requirements --rd <path> [--output review.md] [--models gat/models.yaml] [--logs logs/]`
- `python -m gat hire --rd <path> [--output crew.yaml] [--models gat/models.yaml] [--logs logs/]`
- `python -m gat run --rd <path> --crew <path> [--models gat/models.yaml] [--logs logs/]`

### Behaviour
- Load models via `config_loader.load_models(args.models)`.
- Dispatch to the appropriate phase `run()` function.
- Print the result to stdout.
- On `FileNotFoundError` or `ValueError`, print message to stderr and exit with code 1.
- `__main__.py` simply calls `from gat.cli import main; main()`.

## Acceptance Criteria
- `tests/test_cli.py` passes.
- Entry point `gat = "gat.cli:main"` in `pyproject.toml` works.
- Clean error handling (no tracebacks for user errors).
