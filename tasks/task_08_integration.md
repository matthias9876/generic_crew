# Task 08 – Integration Tests

## Objective
Create integration tests that exercise the full CLI pipeline and validate each module.

## Requirements (from Specification §Testing)
- GAT shall have **unit tests** (pytest) for every module.
- GAT shall have **integration tests** that exercise the full CLI pipeline.
- Every generated crew shall include a dedicated integration-test task.

### Integration tests to implement
1. **Full pipeline test**: `requirements` → `hire` → `run` with mocked LLM calls.
2. **CLI round-trip**: Invoke `main()` with each subcommand and verify outputs.
3. **Config validation round-trip**: Load → validate → use in phase.
4. **Work log integrity**: Run a phase and verify log files are created with correct structure.

### Test file
`tests/test_integration.py`

## Acceptance Criteria
- All existing unit tests still pass.
- Integration tests cover the happy-path pipeline.
- Tests use mocking for LLM calls (no actual Ollama required).
- `pytest tests/` passes with 0 failures.
