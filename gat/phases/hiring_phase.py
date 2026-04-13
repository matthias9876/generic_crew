import os
import yaml
from typing import Dict
from gat import config_loader, work_log

from crewai import Crew, Agent, Task, Process


_HIRING_PROMPT = """\
You are the Hiring Manager for an AI crew. Read the requirements below and produce
a YAML document that defines the agents and tasks needed to fulfil the project.

Rules:
- Each agent needs: name, role, goal, backstory, model (one of: coder, critic, tester, writer), tools (list; valid: shell, python_repl).
- Each task needs: name, description, expected_output, agent (must reference an agent name).
- Only assign tools to agents that need to execute code (coder, tester).
- The critic agent reviews code — it does NOT get tools.
- The writer agent produces documentation — it does NOT get tools.
- Always include a Technical Author agent (model: writer, no tools) with a write_documentation task as the SECOND-TO-LAST task.
- Always include an integration-test task as the FINAL task, assigned to a Tester agent.
- Output ONLY a valid YAML block (no explanatory text outside the YAML).

Top-level keys must be "agents" (list) and "tasks" (list).

Requirements:
{requirements}
"""


def run(rd_path: str, models: Dict, run_dir: str,
        pipeline_cfg: dict = None) -> str:
    """Run the crew hiring phase.

    Writes crew.yaml into run_dir.
    Logs go to run_dir/logs/hiring/.
    Returns the absolute path of crew.yaml.
    """
    if not os.path.isfile(rd_path):
        raise FileNotFoundError(f"Requirements document not found: {rd_path}")

    os.makedirs(run_dir, exist_ok=True)
    log_dir = os.path.join(run_dir, "logs")

    with open(rd_path, 'r', encoding='utf-8') as f:
        requirements = f.read()

    llm = config_loader.make_llm(models, 'requirements', config=pipeline_cfg)

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

    output_yaml_path = os.path.join(run_dir, "crew.yaml")

    last_error = None
    for _ in range(3):
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

    raise ValueError(f"Crew YAML validation failed after 3 attempts: {last_error}")
