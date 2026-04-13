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


# Decorator order: outermost → last mock arg; innermost → first mock arg.
# pytest fixture (tmp_path) must come after all mock args.

@patch("gat.phases.requirements_phase.Crew")           # mock_crew (inner → 1st arg)
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())  # outermost → last arg
def test_output_files_are_created(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, {}, run_dir)
    assert os.path.exists(os.path.join(run_dir, "requirements.md"))
    assert os.path.exists(os.path.join(run_dir, "review.md"))
    assert os.path.exists(os.path.join(run_dir, "requirements_reviewed.md"))


@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_return_value_is_reviewed_path(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    result = requirements_phase.run(rd_path, {}, run_dir)
    assert result == os.path.abspath(os.path.join(run_dir, "requirements_reviewed.md"))


@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_review_document_contains_headings(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, {}, run_dir)
    review = open(os.path.join(run_dir, "review.md")).read()
    assert "# Requirements Review" in review
    assert "## Feasibility Assessment" in review
    assert "FEASIBILITY_OUTPUT" in review


@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_reviewed_doc_contains_original(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Original requirements content")
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, {}, run_dir)
    reviewed = open(os.path.join(run_dir, "requirements_reviewed.md")).read()
    assert "Original requirements content" in reviewed
    assert "FEASIBILITY_OUTPUT" in reviewed


@patch("gat.phases.requirements_phase.Crew")
@patch("gat.phases.requirements_phase.Task", MagicMock)
@patch("gat.phases.requirements_phase.Agent", MagicMock)
@patch("gat.config_loader.make_llm", return_value=MagicMock())
def test_work_log_is_written(mock_llm, mock_crew, tmp_path):
    mock_crew.return_value.kickoff.return_value = _mock_result()
    rd_path = make_temp_file(tmp_path, "Some requirements")
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    requirements_phase.run(rd_path, {}, run_dir)
    log_phase_dir = os.path.join(run_dir, "logs", "requirements")
    assert os.path.isdir(log_phase_dir)
    md_files = [f for f in os.listdir(log_phase_dir) if f.endswith(".md")]
    assert len(md_files) >= 1


def test_missing_requirements_file_raises(tmp_path):
    run_dir = str(tmp_path / "run")
    from gat.phases import requirements_phase
    with pytest.raises(FileNotFoundError):
        requirements_phase.run("/nonexistent/reqs.md", {}, run_dir)
