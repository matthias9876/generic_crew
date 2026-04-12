import os
import pytest
from unittest.mock import patch, MagicMock


def make_temp_file(tmp_path, content):
    f = tmp_path / "reqs.md"
    f.write_text(content)
    return str(f)


def _mock_result():
    task_out_1 = MagicMock()
    task_out_1.raw = "FEASIBILITY_OUTPUT"
    task_out_2 = MagicMock()
    task_out_2.raw = "REQUIREMENTS_OUTPUT"
    result = MagicMock()
    result.tasks_output = [task_out_1, task_out_2]
    return result


@patch("gat.phases.requirements_phase.LLM", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Crew")
def test_output_file_is_created(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    models = {"models": {"large": "ollama/qwen3.5:35b-ctx32k"}}
    log_dir = str(tmp_path / "logs")
    output_path = str(tmp_path / "review.md")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, models, log_dir, output_path)
    assert os.path.exists(output_path)


@patch("gat.phases.requirements_phase.LLM", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Crew")
def test_return_value_equals_abspath(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    models = {"models": {"large": "ollama/qwen3.5:35b-ctx32k"}}
    log_dir = str(tmp_path / "logs")
    output_path = str(tmp_path / "review.md")
    from gat.phases import requirements_phase
    result = requirements_phase.run(rd_path, models, log_dir, output_path)
    assert result == os.path.abspath(output_path)


@patch("gat.phases.requirements_phase.LLM", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Crew")
def test_review_document_contains_headings(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    models = {"models": {"large": "ollama/qwen3.5:35b-ctx32k"}}
    log_dir = str(tmp_path / "logs")
    output_path = str(tmp_path / "review.md")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, models, log_dir, output_path)
    content = open(output_path).read()
    assert "# Requirements Review" in content
    assert "## Feasibility Assessment" in content
    assert "FEASIBILITY_OUTPUT" in content


@patch("gat.phases.requirements_phase.LLM", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Crew")
def test_work_log_is_written(mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    models = {"models": {"large": "ollama/qwen3.5:35b-ctx32k"}}
    log_dir = str(tmp_path / "logs")
    output_path = str(tmp_path / "review.md")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, models, log_dir, output_path)
    log_phase_dir = os.path.join(log_dir, "requirements")
    assert os.path.isdir(log_phase_dir)
    md_files = [f for f in os.listdir(log_phase_dir) if f.endswith(".md")]
    assert len(md_files) >= 1


def test_missing_requirements_file_raises(tmp_path):
    models = {"models": {"large": "ollama/qwen3.5:35b-ctx32k"}}
    log_dir = str(tmp_path / "logs")
    output_path = str(tmp_path / "review.md")
    from gat.phases import requirements_phase
    with pytest.raises(FileNotFoundError):
        requirements_phase.run("/nonexistent/reqs.md", models, log_dir, output_path)
