import os
import sys
import venv
import subprocess
import io
import contextlib
from typing import Dict

from gat import config_loader, work_log
from crewai import Crew, Agent, Task, Process, LLM
from crewai.tools import BaseTool


class ShellTool(BaseTool):
    name: str = "shell"
    description: str = "Run a shell command inside the shared virtual environment and return stdout+stderr."
    _env: dict = {}

    def __init__(self, env: dict, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_env', env)

    def _run(self, command: str) -> str:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=120, env=self._env,
        )
        return result.stdout + result.stderr


class PythonREPLTool(BaseTool):
    name: str = "python_repl"
    description: str = "Execute Python code inside the shared virtual environment and return the output."
    _env: dict = {}

    def __init__(self, env: dict, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_env', env)

    def _run(self, code: str) -> str:
        python = os.path.join(self._env.get('VIRTUAL_ENV', ''), 'bin', 'python3')
        if not os.path.isfile(python):
            python = sys.executable
        result = subprocess.run(
            [python, '-c', code],
            capture_output=True, text=True,
            timeout=120, env=self._env,
        )
        return result.stdout + result.stderr


def _create_shared_venv(venv_dir: str) -> dict:
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True)
    venv_bin = os.path.join(venv_dir, 'bin')
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = venv_dir
    env['PATH'] = venv_bin + os.pathsep + env.get('PATH', '')
    return env


def run(rd_path: str, crew_yaml_path: str, models: dict, log_dir: str) -> str:
    # 1. Load and validate crew YAML
    crew_dict = config_loader.load_crew(crew_yaml_path)
    config_loader.validate_crew(crew_dict, models)

    # 2. Read requirements and prepend to first task
    with open(rd_path, 'r', encoding='utf-8') as f:
        req_content = f.read().strip()
    if crew_dict['tasks']:
        crew_dict['tasks'][0]['description'] = (
            req_content + '\n\n' + crew_dict['tasks'][0]['description']
        )

    # 3. Create shared venv
    venv_dir = os.path.join(log_dir, 'venv')
    env = _create_shared_venv(venv_dir)

    # 4. Build tools
    shell_tool = ShellTool(env=env)
    python_tool = PythonREPLTool(env=env)
    tool_map = {'shell': shell_tool, 'python_repl': python_tool}

    # 5. Build LLMs and Agents
    agent_objs = {}
    for agent_def in crew_dict['agents']:
        model_alias = agent_def['model']
        llm = LLM(model=models['models'][model_alias])
        tools = []
        for t in agent_def.get('tools', []):
            if t in tool_map:
                tools.append(tool_map[t])
        agent_objs[agent_def['name']] = Agent(
            role=agent_def['role'],
            goal=agent_def['goal'],
            backstory=agent_def['backstory'],
            llm=llm,
            tools=tools,
        )

    # 6. Build Tasks
    task_objs = []
    for task_def in crew_dict['tasks']:
        agent_name = task_def['agent']
        task_objs.append(Task(
            description=task_def['description'],
            expected_output=task_def['expected_output'],
            agent=agent_objs[agent_name],
        ))

    # 7. Build and run Crew
    crew = Crew(
        agents=list(agent_objs.values()),
        tasks=task_objs,
        process=Process.sequential,
        verbose=True,
    )
    result = crew.kickoff()

    # 8. Write work logs per agent
    for i, task_def in enumerate(crew_dict['tasks']):
        agent_name = task_def['agent']
        task_output = ""
        if hasattr(result, 'tasks_output') and i < len(result.tasks_output):
            task_output = result.tasks_output[i].raw
        work_log.append_run(
            log_dir=log_dir,
            phase='execution',
            agent_name=agent_name,
            task_description=task_def['description'],
            assigned_by='system',
            thoughts='Execution phase run',
            result=str(task_output),
        )

    return result.raw if hasattr(result, 'raw') else str(result)
