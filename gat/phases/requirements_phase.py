import os
import shutil
from typing import Dict
from gat import config_loader, work_log

from crewai import Crew, Agent, Task, Process


def run(rd_path: str, models: Dict, run_dir: str,
        pipeline_cfg: dict = None) -> str:
    """Run the requirements review phase.

    Writes to run_dir:
      - requirements.md          copy of the original requirements document
      - review.md                feasibility + task breakdown (LLM output)
      - requirements_reviewed.md merged doc the user can edit and re-feed

    Logs go to run_dir/logs/requirements/.
    Returns the absolute path of requirements_reviewed.md.
    """
    if not os.path.isfile(rd_path):
        raise FileNotFoundError(f"Requirements document not found: {rd_path}")

    os.makedirs(run_dir, exist_ok=True)
    log_dir = os.path.join(run_dir, "logs")

    with open(rd_path, 'r', encoding='utf-8') as f:
        requirements_content = f.read()

    # Copy original requirements into the run directory
    shutil.copy2(rd_path, os.path.join(run_dir, "requirements.md"))

    if pipeline_cfg is None:
        pipeline_cfg = config_loader._DEFAULT_CONFIG
    req_cfg = pipeline_cfg.get('requirements', {})
    max_lines = req_cfg.get('max_lines_per_task', 150)
    max_tasks = req_cfg.get('max_tasks', 20)

    llm = config_loader.make_llm(models, 'requirements', config=pipeline_cfg)

    senior_consultant = Agent(
        role="Senior Consultant",
        goal="Assess if the project is advisable and identify major risks.",
        backstory="A highly experienced consultant who provides honest, critical feasibility reviews.",
        llm=llm,
    )
    requirements_engineer = Agent(
        role="Requirements Engineer",
        goal="Break requirements into small, implementable tasks with clear contracts.",
        backstory="A requirements engineering expert who ensures each task is scoped, testable, and well-defined.",
        llm=llm,
    )

    feasibility_task = Task(
        description=(
            f"Feasibility review of the following requirements document:\n\n"
            f"{requirements_content}\n\n"
            f"Determine whether the project is advisable or flag if it is a bad idea. "
            f"Identify major risks."
        ),
        expected_output="A feasibility assessment with risk analysis and a clear recommendation.",
        agent=senior_consultant,
    )
    breakdown_task = Task(
        description=(
            f"Analyse the following requirements document and break it down into "
            f"small, concrete implementation tasks.\n\n"
            f"{requirements_content}\n\n"
            f"Rules for the task breakdown:\n"
            f"- Each task MUST produce at most {max_lines} lines of code.\n"
            f"- Generate at most {max_tasks} tasks.\n"
            f"- Each task must specify: name, description, input contract "
            f"(what it receives from prior tasks), output contract "
            f"(what it produces for subsequent tasks), and acceptance criteria.\n"
            f"- Order tasks by dependency — earlier tasks must not depend on later ones.\n"
            f"- The final task must always be 'integration-test' that validates all "
            f"pieces work together.\n"
            f"- Include a 'write-documentation' task as the second-to-last task.\n\n"
            f"Output a numbered list of tasks in Markdown."
        ),
        expected_output=(
            "A numbered Markdown list of tasks, each with: name, description, "
            "input_contract, output_contract, acceptance_criteria. "
            f"Each task ≤ {max_lines} lines of code. Max {max_tasks} tasks."
        ),
        agent=requirements_engineer,
    )

    crew = Crew(
        agents=[senior_consultant, requirements_engineer],
        tasks=[feasibility_task, breakdown_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    feasibility_output = result.tasks_output[0].raw if result.tasks_output else ""
    breakdown_output = result.tasks_output[1].raw if len(result.tasks_output) > 1 else ""

    # review.md — raw LLM output, structured for later phases
    review_md = f"""# Requirements Review

## Feasibility Assessment
{feasibility_output}

## Task Breakdown
{breakdown_output}
"""
    review_path = os.path.join(run_dir, "review.md")
    with open(review_path, 'w', encoding='utf-8') as f:
        f.write(review_md)

    # requirements_reviewed.md — original + consultant questions/improvements inlined
    # The user can edit this file and pass it as --rd to the next run.
    reviewed_md = f"""# Requirements (Reviewed)

> This file merges your original requirements with the consultant's analysis.
> Edit this file to address questions and improvements, then pass it as --rd to the next phase.

---

## Original Requirements

{requirements_content}

---

## Consultant Feedback

### Feasibility Assessment
{feasibility_output}

### Suggested Task Breakdown
{breakdown_output}
"""
    reviewed_path = os.path.join(run_dir, "requirements_reviewed.md")
    with open(reviewed_path, 'w', encoding='utf-8') as f:
        f.write(reviewed_md)

    work_log.append_run(
        log_dir=log_dir,
        phase="requirements",
        agent_name="Senior Consultant",
        task_description="Feasibility review of the requirements document.",
        assigned_by="system",
        thoughts="N/A",
        result=str(feasibility_output),
    )
    work_log.append_run(
        log_dir=log_dir,
        phase="requirements",
        agent_name="Requirements Engineer",
        task_description="Task breakdown with contracts and size limits.",
        assigned_by="system",
        thoughts="N/A",
        result=str(breakdown_output),
        produced_files=[os.path.abspath(reviewed_path)],
    )

    return os.path.abspath(reviewed_path)
