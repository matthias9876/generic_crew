import os
import yaml
from typing import Dict
from gat import config_loader, work_log

from crewai import Crew, Agent, Task, Process, LLM


_HIRING_PROMPT = """\
You are the Hiring Manager for an AI crew. Read the requirements below and produce
a YAML document that defines the agents and tasks needed to fulfil the project.

Rules:
- Each agent needs: name, role, goal, backstory, model (one of: large, dev, tester), tools (list; valid: shell, python_repl).
- Each task needs: name, description, expected_output, agent (must reference an agent name).
- Only assign tools to agents that need to execute code.
- Always include a Technical Author agent (model: large, no tools) with a write_documentation task as the second-to-last task.
- Always include an integration-test task as the final task, assigned to a Tester agent.
- Output ONLY a valid YAML block (no explanatory text outside the YAML).

Top-level keys must be "agents" (list) and "tasks" (list).

Requirements:
{requirements}
"""


def run(rd_path: str, models: Dict, log_dir: str, output_yaml_path: str) -> str:
    if not os.path.isfile(rd_path):
        raise FileNotFoundError(f"Requirements document not found: {rd_path}")

    with open(rd_path, 'r', encoding='utf-8') as f:
        requirements = f.read()

    model_string = models['models']['large']
    llm = LLM(model=model_string)

    hiring_manager = Agent(
        role="Hiring Manager",
        goal="Analyse requirements and produce a crew YAML that defines agents and tasks for the project.",
        backstory="An expert at assembling AI teams. Reads requirements and outputs structured crew definitions.",
        llm=llm,
    )

    prompt = _HIRING_PROMPT.format(requirements=requirements)

    hiring_task = Task(
        description=prompt,
        expected_output="A valid YAML document with top-level keys 'agents' and 'tasks'.",
        agent=hiring_manager,
    )

    crew = Crew(
        agents=[hiring_manager],
        tasks=[hiring_task],
        process=Process.sequential,
        verbose=True,
    )

    last_error = None
    for attempt in range(2):
        result = crew.kickoff()
        crew_yaml_str = result.raw if hasattr(result, 'raw') else str(result)

        # Strip markdown fences if the LLM wraps output in ```yaml ... ```
        cleaned = crew_yaml_str.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]  # drop opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = yaml.safe_load(cleaned)
            config_loader.validate_crew(data, models)

            out_dir = os.path.dirname(output_yaml_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)

            work_log.append_run(
                log_dir=log_dir,
                phase="hiring",
                agent_name="Hiring Manager",
                task_description="Generate crew YAML from requirements",
                assigned_by="system",
                thoughts=prompt,
                result=crew_yaml_str,
                produced_files=[os.path.abspath(output_yaml_path)],
            )
            return os.path.abspath(output_yaml_path)
        except Exception as e:
            last_error = e

    raise ValueError(f"Crew YAML validation failed after 2 attempts: {last_error}")
