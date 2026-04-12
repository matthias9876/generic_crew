import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


def make_temp_file(tmp_path, content, filename="file.txt"):
    f = tmp_path / filename
    f.write_text(content)
    return str(f)


MODELS = {
    "models": {
        "large": "ollama/qwen3.5:35b-ctx32k",
        "dev": "ollama/qwen3.5:9b-ctx16k",
        "tester": "ollama/mistral:ctx16k",
    }
}

CREW_DICT = {
    "agents": [
        {"name": "Dev", "role": "Developer", "goal": "Write code",
         "backstory": "Expert", "model": "dev", "tools": ["shell", "python_repl"]},
    ],
    "tasks": [
        {"name": "implement", "description": "Task desc",
         "expected_output": "Working code", "agent": "Dev"},
    ],
}


def _mock_result():
    task_out = MagicMock()
    task_out.raw = "TASK_RESULT"
    result = MagicMock()
    result.raw = "FINAL_RESULT"
    result.tasks_output = [task_out]
    return result


@patch("gat.phases.execution_phase.LLM", MagicMock)
@patch("gat.phases.execution_phase.Agent", MagicMock)
@patch("gat.phases.execution_phase.Task", MagicMock)
@patch("gat.phases.execution_phase.Crew")
@patch("gat.phases.execution_phase.config_loader")
@patch("gat.phases.execution_phase.work_log")
def test_run_returns_result(mock_wl, mock_cl, mock_crew, tmp_path):
    mock_cl.load_crew.return_value = CREW_DICT.copy()
    mock_cl.load_crew.return_value["tasks"] = [t.copy() for t in CREW_DICT["tasks"]]
    mock_cl.validate_crew.return_value = None
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "REQS", "reqs.md")
    crew_yaml = make_temp_file(tmp_path, "yaml", "crew.yaml")
    log_dir = str(tmp_path / "logs")
    from gat.phases import execution_phase
    result = execution_phase.run(rd_path, crew_yaml, MODELS, log_dir)
    assert result == "FINAL_RESULT"
    mock_cl.load_crew.assert_called_once_with(crew_yaml)
    mock_cl.validate_crew.assert_called_once()
    assert mock_wl.append_run.called


@patch("gat.phases.execution_phase.LLM", MagicMock)
@patch("gat.phases.execution_phase.Agent", MagicMock)
@patch("gat.phases.execution_phase.Task", MagicMock)
@patch("gat.phases.execution_phase.Crew")
@patch("gat.phases.execution_phase.config_loader")
@patch("gat.phases.execution_phase.work_log")
def test_run_prepends_requirements(mock_wl, mock_cl, mock_crew, tmp_path):
    crew_copy = {
        "agents": list(CREW_DICT["agents"]),
        "tasks": [t.copy() for t in CREW_DICT["tasks"]],
    }
    mock_cl.load_crew.return_value = crew_copy
    mock_cl.validate_crew.return_value = None
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "REQS", "reqs.md")
    crew_yaml = make_temp_file(tmp_path, "yaml", "crew.yaml")
    log_dir = str(tmp_path / "logs")
    from gat.phases import execution_phase
    execution_phase.run(rd_path, crew_yaml, MODELS, log_dir)
    assert crew_copy["tasks"][0]["description"].startswith("REQS\n")


@patch("gat.phases.execution_phase.LLM", MagicMock)
@patch("gat.phases.execution_phase.Agent", MagicMock)
@patch("gat.phases.execution_phase.Task", MagicMock)
@patch("gat.phases.execution_phase.Crew")
@patch("gat.phases.execution_phase.config_loader")
@patch("gat.phases.execution_phase.work_log")
def test_venv_created(mock_wl, mock_cl, mock_crew, tmp_path):
    mock_cl.load_crew.return_value = {
        "agents": list(CREW_DICT["agents"]),
        "tasks": [t.copy() for t in CREW_DICT["tasks"]],
    }
    mock_cl.validate_crew.return_value = None
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "REQS", "reqs.md")
    crew_yaml = make_temp_file(tmp_path, "yaml", "crew.yaml")
    log_dir = str(tmp_path / "logs")
    from gat.phases import execution_phase
    execution_phase.run(rd_path, crew_yaml, MODELS, log_dir)
    venv_dir = os.path.join(log_dir, "venv")
    assert os.path.isdir(venv_dir)
