import os
import re
import pytest
from gat import work_log

def test_file_created_on_first_call(tmp_path):
    path = work_log.append_run(
        log_dir=str(tmp_path),
        phase="requirements",
        agent_name="Consultant",
        task_description="Write requirements",
        assigned_by="Lead",
        thoughts="Thinking...",
        result="Done."
    )
    assert os.path.exists(path)
    assert path.endswith(os.path.join("requirements", "Consultant.md"))

def test_directory_created_automatically(tmp_path):
    log_dir = tmp_path / "logs" / "nested"
    path = work_log.append_run(
        log_dir=str(log_dir),
        phase="design",
        agent_name="Architect",
        task_description="Design system",
        assigned_by="Lead",
        thoughts="Designing...",
        result="Design complete."
    )
    assert os.path.exists(path)
    assert path.endswith(os.path.join("design", "Architect.md"))

def test_content_is_correct(tmp_path):
    path = work_log.append_run(
        log_dir=str(tmp_path),
        phase="plan",
        agent_name="Planner",
        task_description="Plan project",
        assigned_by="Lead",
        thoughts="Planning...",
        result="Planned."
    )
    content = open(path, encoding="utf-8").read()
    assert "**Task:**" in content
    assert "**Assigned by:**" in content
    assert "### Thoughts" in content
    assert "### Result" in content
    assert "---" in content

def test_produced_files_section_present(tmp_path):
    path = work_log.append_run(
        log_dir=str(tmp_path),
        phase="output",
        agent_name="Producer",
        task_description="Produce files",
        assigned_by="Lead",
        thoughts="Producing...",
        result="Files produced.",
        produced_files=["output/report.md"]
    )
    content = open(path, encoding="utf-8").read()
    assert "### Produced Files" in content
    assert "[report.md]" in content

def test_produced_files_section_absent(tmp_path):
    path = work_log.append_run(
        log_dir=str(tmp_path),
        phase="output",
        agent_name="Producer",
        task_description="Produce files",
        assigned_by="Lead",
        thoughts="Producing...",
        result="Files produced.",
        produced_files=[]
    )
    content = open(path, encoding="utf-8").read()
    assert "### Produced Files" not in content

def test_multiple_runs_append(tmp_path):
    path = work_log.append_run(
        log_dir=str(tmp_path),
        phase="run",
        agent_name="Runner",
        task_description="Run 1",
        assigned_by="Lead",
        thoughts="First run",
        result="Result 1"
    )
    path2 = work_log.append_run(
        log_dir=str(tmp_path),
        phase="run",
        agent_name="Runner",
        task_description="Run 2",
        assigned_by="Lead",
        thoughts="Second run",
        result="Result 2"
    )
    assert path == path2
    content = open(path, encoding="utf-8").read()
    assert "Result 1" in content
    assert "Result 2" in content
    # Count number of headings
    runs = re.findall(r"^## Run — ", content, re.MULTILINE)
    assert len(runs) == 2
