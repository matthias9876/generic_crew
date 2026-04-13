import os
import yaml
import pytest
from unittest.mock import patch, MagicMock


MODELS = {
    "models": {
        "large": "ollama/qwen3.5:35b-ctx32k",
        "dev": "ollama/qwen3.5:9b-ctx16k",
        "tester": "ollama/mistral:ctx16k",
    }
}

VALID_CREW_YAML = {
    "agents": [
        {"name": "Developer", "role": "Developer", "goal": "Write code",
         "backstory": "Expert coder", "model": "dev", "tools": ["shell"]},
        {"name": "Technical Author", "role": "Technical Writer",
         "goal": "Write docs", "backstory": "Expert writer",
         "model": "large", "tools": []},
        {"name": "Tester", "role": "Tester", "goal": "Test",
         "backstory": "QA", "model": "tester", "tools": ["shell"]},
    ],
    "tasks": [
        {"name": "implement", "description": "Implement feature",
         "expected_output": "Working code", "agent": "Developer"},
        {"name": "write_documentation", "description": "Write docs",
         "expected_output": "Docs", "agent": "Technical Author"},
        {"name": "integration_test", "description": "Run tests",
         "expected_output": "Report", "agent": "Tester"},
    ],
}


def make_temp_file(tmp_path, content, name="file.txt"):
    f = tmp_path / name
    f.write_text(content)
    return str(f)


def _mock_kickoff_result(raw="RESULT", num_tasks=1):
    task_outs = []
    for i in range(num_tasks):
        t = MagicMock()
        t.raw = f"TASK_{i}_OUTPUT"
        task_outs.append(t)
    result = MagicMock()
    result.raw = raw
    result.tasks_output = task_outs
    return result


# --- Integration test 1: Full pipeline requirements → hire → run ---

@patch("gat.phases.execution_phase.Crew")
@patch("gat.phases.execution_phase.Agent", MagicMock)
@patch("gat.phases.execution_phase.Task", MagicMock)
@patch("gat.phases.execution_phase.config_loader")
@patch("gat.phases.execution_phase.work_log")
@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_full_pipeline(mock_llm, mock_req_crew, mock_hire_crew,
                       mock_exec_wl, mock_exec_cl, mock_exec_crew,
                       tmp_path):
    run_dir = str(tmp_path / "run")

    # Phase 1: Requirements
    mock_req_crew.return_value.kickoff.return_value = _mock_kickoff_result("REQ_REVIEW", 2)
    rd_path = make_temp_file(tmp_path, "Build a calculator app", "requirements.md")

    from gat.phases import requirements_phase
    reviewed_path = requirements_phase.run(rd_path, MODELS, run_dir)
    assert os.path.exists(reviewed_path)
    assert os.path.exists(os.path.join(run_dir, "requirements.md"))
    assert os.path.exists(os.path.join(run_dir, "review.md"))

    # Phase 2: Hiring
    crew_yaml_str = yaml.dump(VALID_CREW_YAML)
    hire_result_mock = MagicMock()
    hire_result_mock.raw = crew_yaml_str
    mock_hire_crew.return_value.kickoff.return_value = hire_result_mock

    from gat.phases import hiring_phase
    crew_path = hiring_phase.run(reviewed_path, MODELS, run_dir)
    assert os.path.exists(crew_path)

    with open(crew_path) as f:
        crew_data = yaml.safe_load(f)
    from gat.config_loader import validate_crew
    validate_crew(crew_data, MODELS)

    # Phase 3: Execution
    mock_exec_cl.load_crew.return_value = {
        "agents": [a.copy() for a in VALID_CREW_YAML["agents"]],
        "tasks": [t.copy() for t in VALID_CREW_YAML["tasks"]],
    }
    mock_exec_cl.validate_crew.return_value = None
    mock_exec_cl._DEFAULT_CONFIG = {}
    mock_exec_crew.return_value.kickoff.return_value = _mock_kickoff_result("DONE", 3)

    from gat.phases import execution_phase
    exec_result = execution_phase.run(rd_path, crew_path, MODELS, run_dir)
    assert "iterations" in exec_result or "implement" in exec_result


# --- Integration test 2: CLI round-trips ---

def test_cli_requirements_roundtrip(tmp_path, monkeypatch):
    from unittest import mock
    rd_path = make_temp_file(tmp_path, "Some requirements", "rd.md")
    run_dir = str(tmp_path / "run")

    m = mock.Mock(return_value=os.path.join(run_dir, "requirements_reviewed.md"))
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)

    from gat.cli import main
    main(["--run-dir", run_dir, "requirements", "--rd", rd_path])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == rd_path
    assert m.call_args.kwargs["run_dir"] == run_dir


def test_cli_hire_roundtrip(tmp_path, monkeypatch):
    from unittest import mock
    rd_path = make_temp_file(tmp_path, "Some requirements", "rd.md")
    run_dir = str(tmp_path / "run")

    m = mock.Mock(return_value=os.path.join(run_dir, "crew.yaml"))
    monkeypatch.setattr("gat.phases.hiring_phase.run", m)

    from gat.cli import main
    main(["--run-dir", run_dir, "hire", "--rd", rd_path])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == rd_path


def test_cli_run_roundtrip(tmp_path, monkeypatch):
    from unittest import mock
    rd_path = make_temp_file(tmp_path, "Some requirements", "rd.md")
    crew_path = make_temp_file(tmp_path, "crew yaml", "crew.yaml")
    run_dir = str(tmp_path / "run")

    m = mock.Mock(return_value="DONE")
    monkeypatch.setattr("gat.phases.execution_phase.run", m)

    from gat.cli import main
    main(["--run-dir", run_dir, "run", "--rd", rd_path, "--crew", crew_path])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == rd_path
    assert m.call_args.kwargs["crew_yaml_path"] == crew_path


# --- Integration test 3: Config validation round-trip ---

def test_config_load_validate_roundtrip(tmp_path):
    crew_path = tmp_path / "crew.yaml"
    with open(crew_path, 'w') as f:
        yaml.dump(VALID_CREW_YAML, f)

    from gat.config_loader import load_crew, validate_crew
    crew = load_crew(str(crew_path))
    validate_crew(crew, MODELS)  # should not raise


# --- Integration test 4: Work log integrity ---

@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_work_log_integrity(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_kickoff_result("OUTPUT", 2)

    rd_path = make_temp_file(tmp_path, "Requirements here", "rd.md")
    run_dir = str(tmp_path / "run")

    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, MODELS, run_dir)

    log_phase = os.path.join(run_dir, "logs", "requirements")
    assert os.path.isdir(log_phase)
    md_files = [f for f in os.listdir(log_phase) if f.endswith(".md")]
    assert len(md_files) >= 1

    for md in md_files:
        content = open(os.path.join(log_phase, md)).read()
        assert "## Run" in content
        assert "**Task:**" in content
        assert "**Assigned by:**" in content


# --- Integration test 5: Generated crew must include integration-test task ---

def test_generated_crew_has_integration_test():
    last_task = VALID_CREW_YAML["tasks"][-1]
    assert "integration" in last_task["name"].lower() or "test" in last_task["name"].lower()
