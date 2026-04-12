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


@patch("gat.phases.hiring_phase.LLM", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Crew")
def test_happy_path_writes_yaml(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result(VALID_CREW_YAML)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    output = str(tmp_path / "crew.yaml")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, str(tmp_path / "logs"), output)
    assert result == os.path.abspath(output)
    assert os.path.exists(output)
    data = yaml.safe_load(open(output))
    assert "agents" in data
    assert "tasks" in data


@patch("gat.phases.hiring_phase.LLM", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Crew")
def test_strips_markdown_fences(mock_crew, tmp_path):
    fenced = "```yaml\n" + VALID_CREW_YAML + "\n```"
    mock_crew.return_value.kickoff.return_value = _mock_result(fenced)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    output = str(tmp_path / "crew.yaml")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, str(tmp_path / "logs"), output)
    assert os.path.exists(output)


@patch("gat.phases.hiring_phase.LLM", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Crew")
def test_retries_on_invalid_yaml(mock_crew, tmp_path):
    good = _mock_result(VALID_CREW_YAML)
    bad = _mock_result("not: valid: crew: yaml")
    mock_crew.return_value.kickoff.side_effect = [bad, good]
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    output = str(tmp_path / "crew.yaml")
    from gat.phases import hiring_phase
    result = hiring_phase.run(rd_path, MODELS, str(tmp_path / "logs"), output)
    assert os.path.exists(output)


@patch("gat.phases.hiring_phase.LLM", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Crew")
def test_raises_after_two_failures(mock_crew, tmp_path):
    bad = _mock_result("garbage")
    mock_crew.return_value.kickoff.return_value = bad
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    output = str(tmp_path / "crew.yaml")
    from gat.phases import hiring_phase
    with pytest.raises(ValueError, match="validation failed"):
        hiring_phase.run(rd_path, MODELS, str(tmp_path / "logs"), output)


def test_missing_rd_raises(tmp_path):
    from gat.phases import hiring_phase
    with pytest.raises(FileNotFoundError):
        hiring_phase.run("/nonexistent/rd.md", MODELS, str(tmp_path / "logs"), str(tmp_path / "crew.yaml"))


@patch("gat.phases.hiring_phase.LLM", MagicMock)
@patch("gat.phases.hiring_phase.Agent", MagicMock)
@patch("gat.phases.hiring_phase.Task", MagicMock)
@patch("gat.phases.hiring_phase.Crew")
def test_work_log_written(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result(VALID_CREW_YAML)
    rd_path = make_temp_file(tmp_path, "Build a calculator")
    log_dir = str(tmp_path / "logs")
    output = str(tmp_path / "crew.yaml")
    from gat.phases import hiring_phase
    hiring_phase.run(rd_path, MODELS, log_dir, output)
    log_phase_dir = os.path.join(log_dir, "hiring")
    assert os.path.isdir(log_phase_dir)
