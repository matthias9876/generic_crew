import os
from typing import Dict
from gat import config_loader, work_log

from crewai import Crew, Agent, Task, Process, LLM


def run(rd_path: str, models: Dict, log_dir: str, output_path: str) -> str:
    if not os.path.isfile(rd_path):
        raise FileNotFoundError(f"Requirements document not found: {rd_path}")

    with open(rd_path, 'r', encoding='utf-8') as f:
        requirements_content = f.read()

    llm = LLM(model=models['models']['large'])

    senior_consultant = Agent(
        role="Senior Consultant",
        goal="Assess if the project is advisable and identify major risks.",
        backstory="A highly experienced consultant who provides honest, critical feasibility reviews.",
        llm=llm,
    )
    requirements_engineer = Agent(
        role="Requirements Engineer",
        goal="Find ambiguities, ask clarification questions, and suggest improvements to the requirements.",
        backstory="A requirements engineering expert who ensures requirements are clear and actionable.",
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
    requirements_task = Task(
        description=(
            f"Requirements analysis of the following document:\n\n"
            f"{requirements_content}\n\n"
            f"Identify ambiguities, ask clarification questions, and suggest improvements."
        ),
        expected_output=(
            "A structured analysis with sections: "
            "clarification_questions (list) and suggested_improvements (text)."
        ),
        agent=requirements_engineer,
    )

    crew = Crew(
        agents=[senior_consultant, requirements_engineer],
        tasks=[feasibility_task, requirements_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    feasibility_output = result.tasks_output[0].raw if result.tasks_output else ""
    requirements_output = result.tasks_output[1].raw if len(result.tasks_output) > 1 else ""

    review_md = f"""# Requirements Review

## Feasibility Assessment
{feasibility_output}

## Clarification Questions & Suggested Improvements
{requirements_output}
"""
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(review_md)

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
        task_description="Requirements analysis: identify ambiguities, clarification questions, and suggest improvements.",
        assigned_by="system",
        thoughts="N/A",
        result=str(requirements_output),
    )

    return os.path.abspath(output_path)
