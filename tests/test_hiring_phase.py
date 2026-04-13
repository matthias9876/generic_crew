import os
import yaml
import pytest
from unittest.mock import patch, MagicMock


VALID_CREW_YAML = """\
agents:
  - name: Developer
    role: Developer
    goal: Write code
    backstory: Expert coder
    model: dev
    tools:
      - shell
      - python_repl
  - name: Technical Author
    role: Technical Writer
    goal: Write documentation
    backstory: Expert writer
    model: large
    tools: []
  - name: Tester
    role: Tester
    goal: Test the project
    backstory: QA specialist
    model: tester
    tools:
      - shell
tasks:
  - name: implement
    description: Implement the feature
    expected_output: Working code
    agent: Developer
  - name: write_documentation
    description: Write docs
    expected_output: Markdown documentation
    agent: Technical Author
  - name: integration_test
    description: Run integration tests
    expected_output: Test report
    agent: Tester
"""

MODELS = {
    "models": {
        "large": "ollama/qwen3.5:35b-ctx32k",
        "dev": "ollama/qwen3.5:9b-ctx16k",
        "tester": "ollama/mistral:ctx16k",
    }
}


def make_temp_file(tmp_path, content, name="reqs.md"):
    f = tmp_path / name
    f.write_text(content)
    return str(f)


def _mock_result(raw_text):
    result = MagicMock()
    result.raw = raw_text
    return result


@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_happy_path_writes_yaml(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result(VALID_CREW_YAML)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    run_dir = str(tmp_path / "run")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, run_dir)
    crew_yaml = os.path.join(run_dir, "crew.yaml")
    assert result == os.path.abspath(crew_yaml)
    assert os.path.exists(crew_yaml)
    data = yaml.safe_load(open(crew_yaml))
    assert "agents" in data
    assert "tasks" in data


@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_strips_markdown_fences(mock_llm, mock_crew, tmp_path):
    fenced = "```yaml\n" + VALID_CREW_YAML + "\n```"
    mock_crew.return_value.kickoff.return_value = _mock_result(fenced)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    run_dir = str(tmp_path / "run")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, run_dir)
    assert os.path.exists(os.path.join(run_dir, "crew.yaml"))


@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_retries_on_invalid_yaml(mock_llm, mock_crew, tmp_path):
    good = _mock_result(VALID_CREW_YAML)
    bad = _mock_result("not: valid: crew: yaml")
    mock_crew.return_value.kickoff.side_effect = [bad, good]
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    run_dir = str(tmp_path / "run")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, run_dir)
    assert os.path.exists(os.path.join(run_dir, "crew.yaml"))


@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_raises_after_two_failures(mock_llm, mock_crew, tmp_path):
    bad = _mock_result("garbage")
    mock_crew.return_value.kickoff.return_value = bad
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    run_dir = str(tmp_path / "run")
    from gat.phases import hiring_phase
    with pytest.raises(ValueError, match="validation failed"):
        hiring_phase.run(rd_path, MODELS, run_dir)


def test_missing_rd_raises(tmp_path):
    from gat.phases import hiring_phase
    with pytest.raises(FileNotFoundError):
        hiring_phase.run("/nonexistent/rd.md", MODELS, str(tmp_path / "run"))


@patch("gat.phases.hiring_phase.Crew")
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_work_log_written(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result(VALID_CREW_YAML)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    run_dir = str(tmp_path / "run")
    from gat.phases import hiring_phase
    hiring_phase.run(rd_path, MODELS, run_dir)
    log_phase_dir = os.path.join(run_dir, "logs", "hiring")
    assert os.path.isdir(log_phase_dir)
