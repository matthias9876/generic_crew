import os
import sys
import venv
import subprocess
from typing import Dict, List

from gat import config_loader, work_log
from crewai import Crew, Agent, Task, Process, LLM
from crewai.tools import BaseTool


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

class ShellTool(BaseTool):
    name: str = "shell"
    description: str = "Run a shell command inside the shared virtual environment and return stdout+stderr."
    _env: dict = {}
    _timeout: int = 120

    def __init__(self, env: dict, timeout: int = 120, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_env', env)
        object.__setattr__(self, '_timeout', timeout)

    def _run(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=self._timeout, env=self._env,
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"ERROR: Command timed out after {self._timeout}s: {command[:120]}"


class PythonREPLTool(BaseTool):
    name: str = "python_repl"
    description: str = "Execute Python code inside the shared virtual environment and return the output."
    _env: dict = {}
    _timeout: int = 120

    def __init__(self, env: dict, timeout: int = 120, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_env', env)
        object.__setattr__(self, '_timeout', timeout)

    def _run(self, code: str) -> str:
        python = os.path.join(self._env.get('VIRTUAL_ENV', ''), 'bin', 'python3')
        if not os.path.isfile(python):
            python = sys.executable
        try:
            result = subprocess.run(
                [python, '-c', code],
                capture_output=True, text=True,
                timeout=self._timeout, env=self._env,
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"ERROR: Python execution timed out after {self._timeout}s"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_shared_venv(venv_dir: str) -> dict:
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True)
    venv_bin = os.path.join(venv_dir, 'bin')
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = venv_dir
    env['PATH'] = venv_bin + os.pathsep + env.get('PATH', '')
    return env


def _classify_tasks(tasks: list) -> dict:
    """Split crew tasks into coding, critic, integration, and documentation."""
    coding = []
    critic = []
    integration = []
    documentation = []
    for t in tasks:
        name_lower = t['name'].lower()
        if 'critic' in name_lower or 'review' in name_lower:
            critic.append(t)
        elif 'integration' in name_lower or 'test' in name_lower:
            integration.append(t)
        elif 'document' in name_lower or 'write_doc' in name_lower:
            documentation.append(t)
        else:
            coding.append(t)
    return {
        'coding': coding,
        'critic': critic,
        'integration': integration,
        'documentation': documentation,
    }


def _build_agent(agent_def: dict, models: dict, tool_map: dict) -> Agent:
    model_alias = agent_def['model']
    model_str = models['models'][model_alias]
    llm = LLM(model=model_str)
    tools = []
    for t in agent_def.get('tools', []):
        if t in tool_map:
            tools.append(tool_map[t])
    return Agent(
        role=agent_def['role'],
        goal=agent_def['goal'],
        backstory=agent_def['backstory'],
        llm=llm,
        tools=tools,
    )


def _run_single_task(task_def: dict, agent: Agent, context: str = "") -> str:
    """Run one CrewAI task and return the raw output string."""
    description = task_def['description']
    if context:
        description = context + "\n\n" + description

    task = Task(
        description=description,
        expected_output=task_def['expected_output'],
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    try:
        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)
    except Exception as e:
        error_msg = f"TASK FAILED: {type(e).__name__}: {e}"
        print(f"[execution_phase] {error_msg}", flush=True)
        return error_msg


_CRITIC_VERDICT_PASS = "PASS"
_CRITIC_VERDICT_REWORK = "REWORK"


def _parse_critic_verdict(output: str) -> str:
    """Extract verdict from critic output. Default to PASS if unclear."""
    upper = output.upper()
    if _CRITIC_VERDICT_REWORK in upper:
        return _CRITIC_VERDICT_REWORK
    return _CRITIC_VERDICT_PASS


_INTEGRATION_VERDICT_PASS = "PASS"
_INTEGRATION_VERDICT_FAIL = "FAIL"


def _parse_integration_verdict(output: str) -> str:
    upper = output.upper()
    if _INTEGRATION_VERDICT_FAIL in upper:
        return _INTEGRATION_VERDICT_FAIL
    return _INTEGRATION_VERDICT_PASS


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(rd_path: str, crew_yaml_path: str, models: dict, log_dir: str,
        pipeline_cfg: dict = None) -> str:
    """Execute the iterative pipeline:
    [coding → critics]×N → [integration-test → re-run]×M → documentation (always last).
    """
    # 1. Load config limits
    if pipeline_cfg is None:
        pipeline_cfg = config_loader._DEFAULT_CONFIG
    exec_cfg = pipeline_cfg.get('execution', {})
    tool_cfg = pipeline_cfg.get('tools', {})

    max_cc_cycles = exec_cfg.get('max_coding_critic_cycles', 3)
    max_integ_retries = exec_cfg.get('max_integration_retries', 2)
    max_total = exec_cfg.get('max_total_iterations', 5)
    shell_timeout = tool_cfg.get('shell_timeout', 120)
    python_timeout = tool_cfg.get('python_timeout', 120)

    # 2. Load and validate crew YAML
    crew_dict = config_loader.load_crew(crew_yaml_path)
    config_loader.validate_crew(crew_dict, models)

    # 3. Read requirements
    with open(rd_path, 'r', encoding='utf-8') as f:
        req_content = f.read().strip()

    # 4. Create shared venv & tools
    venv_dir = os.path.join(log_dir, 'venv')
    env = _create_shared_venv(venv_dir)

    shell_tool = ShellTool(env=env, timeout=shell_timeout)
    python_tool = PythonREPLTool(env=env, timeout=python_timeout)
    tool_map = {'shell': shell_tool, 'python_repl': python_tool}

    # 5. Build agents
    agent_objs = {}
    for agent_def in crew_dict['agents']:
        agent_objs[agent_def['name']] = _build_agent(agent_def, models, tool_map)

    # 6. Classify tasks
    classified = _classify_tasks(crew_dict['tasks'])
    coding_tasks = classified['coding']
    critic_tasks = classified['critic']
    integration_tasks = classified['integration']
    doc_tasks = classified['documentation']

    # If no explicit critic task in YAML, build a default one
    if not critic_tasks and coding_tasks:
        critic_tasks = [{
            'name': 'code_review',
            'description': (
                'Review the code produced so far. Check for correctness, '
                'integration fitness, and adherence to the requirements. '
                'End your response with PASS if the code is acceptable, '
                'or REWORK if changes are needed (explain what to fix).'
            ),
            'expected_output': 'A review ending with PASS or REWORK.',
            'agent': next(
                (a['name'] for a in crew_dict['agents']
                 if a.get('model') == 'critic'),
                crew_dict['agents'][0]['name']
            ),
        }]

    if not integration_tasks and coding_tasks:
        integration_tasks = [{
            'name': 'integration_test',
            'description': (
                'Write and execute integration tests that verify all '
                'components work together. Run the tests. '
                'End your response with PASS if all tests pass, '
                'or FAIL if any test fails (include the failure details).'
            ),
            'expected_output': 'Test results ending with PASS or FAIL.',
            'agent': next(
                (a['name'] for a in crew_dict['agents']
                 if a.get('model') == 'tester'),
                crew_dict['agents'][0]['name']
            ),
        }]

    # 7. Execute the iterative pipeline
    total_iterations = 0
    coding_outputs = {}  # task_name -> last output
    all_feedback = []    # accumulated critic/integration feedback

    for integ_round in range(max_integ_retries + 1):
        if total_iterations >= max_total:
            break

        # ── Coding + Critics loop ──
        for coding_task in coding_tasks:
            if total_iterations >= max_total:
                break

            agent_name = coding_task['agent']
            agent = agent_objs.get(agent_name)
            if not agent:
                continue

            for cc_cycle in range(max_cc_cycles):
                if total_iterations >= max_total:
                    break
                total_iterations += 1

                # Build context from requirements + prior feedback
                context_parts = [req_content]
                if all_feedback:
                    context_parts.append(
                        "Previous feedback to address:\n" +
                        "\n---\n".join(all_feedback[-3:])
                    )

                # Run coding task
                coding_output = _run_single_task(
                    coding_task, agent,
                    context="\n\n".join(context_parts)
                )
                coding_outputs[coding_task['name']] = coding_output

                work_log.append_run(
                    log_dir=log_dir,
                    phase='execution',
                    agent_name=agent_name,
                    task_description=coding_task['description'],
                    assigned_by='system',
                    thoughts=f'Coding cycle {cc_cycle + 1}, integration round {integ_round + 1}',
                    result=str(coding_output),
                )

                # Run critic
                if critic_tasks and total_iterations < max_total:
                    critic_task = critic_tasks[0]
                    critic_agent_name = critic_task['agent']
                    critic_agent = agent_objs.get(critic_agent_name)
                    if critic_agent:
                        critic_context = (
                            f"Code output to review:\n{coding_output}\n\n"
                            f"End with PASS or REWORK."
                        )
                        critic_output = _run_single_task(
                            critic_task, critic_agent,
                            context=critic_context
                        )
                        work_log.append_run(
                            log_dir=log_dir,
                            phase='execution',
                            agent_name=critic_agent_name,
                            task_description=critic_task['description'],
                            assigned_by='system',
                            thoughts=f'Critic cycle {cc_cycle + 1}',
                            result=str(critic_output),
                        )

                        verdict = _parse_critic_verdict(critic_output)
                        if verdict == _CRITIC_VERDICT_PASS:
                            break  # move to next coding task
                        else:
                            all_feedback.append(critic_output)
                else:
                    break  # no critic, single pass

        # ── Integration test ──
        if total_iterations >= max_total:
            break

        if integration_tasks:
            integ_task = integration_tasks[0]
            integ_agent_name = integ_task['agent']
            integ_agent = agent_objs.get(integ_agent_name)
            if integ_agent:
                total_iterations += 1
                integ_context = (
                    f"All coding outputs:\n" +
                    "\n---\n".join(
                        f"### {name}\n{out}"
                        for name, out in coding_outputs.items()
                    ) +
                    "\n\nEnd with PASS or FAIL."
                )
                integ_output = _run_single_task(
                    integ_task, integ_agent,
                    context=integ_context
                )
                work_log.append_run(
                    log_dir=log_dir,
                    phase='execution',
                    agent_name=integ_agent_name,
                    task_description=integ_task['description'],
                    assigned_by='system',
                    thoughts=f'Integration round {integ_round + 1}',
                    result=str(integ_output),
                )

                verdict = _parse_integration_verdict(integ_output)
                if verdict == _INTEGRATION_VERDICT_PASS:
                    break  # exit integration retry loop → proceed to docs
                else:
                    all_feedback.append(integ_output)
                    # loop continues → re-run coding+critics
        else:
            break  # no integration tasks → proceed to docs

    # 8. Documentation — ALWAYS runs last
    doc_output = ""
    if doc_tasks:
        doc_task = doc_tasks[0]
        doc_agent_name = doc_task['agent']
        doc_agent = agent_objs.get(doc_agent_name)
        if doc_agent:
            doc_context = (
                f"Requirements:\n{req_content}\n\n"
                f"Implementation outputs:\n" +
                "\n---\n".join(
                    f"### {name}\n{out}"
                    for name, out in coding_outputs.items()
                )
            )
            doc_output = _run_single_task(
                doc_task, doc_agent,
                context=doc_context
            )
            work_log.append_run(
                log_dir=log_dir,
                phase='execution',
                agent_name=doc_agent_name,
                task_description=doc_task['description'],
                assigned_by='system',
                thoughts='Documentation phase (always runs last)',
                result=str(doc_output),
            )

    # 9. Summary
    summary_parts = []
    summary_parts.append(f"Total iterations used: {total_iterations}/{max_total}")
    for name, out in coding_outputs.items():
        summary_parts.append(f"[{name}]: {out[:200]}...")
    if doc_output:
        summary_parts.append(f"[documentation]: {doc_output[:200]}...")
    return "\n\n".join(summary_parts)
