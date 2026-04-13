import os
import yaml
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Built-in defaults (same values as the shipped gat/gat.yaml).
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG = {
    'presets': {},
    'default_preset': 'gpu',
    'requirements': {
        'max_lines_per_task': 150,
        'max_tasks': 20,
    },
    'execution': {
        'max_coding_critic_cycles': 3,
        'max_integration_retries': 2,
        'max_total_iterations': 5,
    },
    'timeouts': {
        'requirements_task': 300,
        'hiring_task': 300,
        'coding_task': 300,
        'critic_task': 180,
        'integration_task': 300,
        'documentation_task': 300,
    },
    'tools': {
        'shell_timeout': 120,
        'python_timeout': 120,
    },
}


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge *overrides* into a copy of *base*."""
    merged = base.copy()
    for key, val in overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = _deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    """Load gat.yaml and merge with built-in defaults.

    Returns the full configuration dict (presets + pipeline settings).
    """
    if path and os.path.isfile(path):
        with open(path, 'r') as f:
            user_cfg = yaml.safe_load(f) or {}
        return _deep_merge(_DEFAULT_CONFIG, user_cfg)
    return _DEFAULT_CONFIG.copy()


def resolve_preset(config: dict, preset: Optional[str] = None) -> dict:
    """Return the models sub-dict for the chosen preset.

    The returned dict has at least a ``models`` key.
    """
    presets = config.get('presets', {})
    if not presets:
        if 'models' in config:
            return {'models': config['models']}
        raise ValueError("No presets defined in configuration.")

    if preset is None:
        preset = config.get('default_preset')
    if preset is None:
        preset = next(iter(presets))

    if preset not in presets:
        available = ', '.join(presets.keys())
        raise ValueError(f"Unknown preset '{preset}'. Available: {available}")

    return presets[preset]


def make_llm(preset_data: dict, role: str):
    """Create a CrewAI LLM for the given role.

    Context window size is controlled by the Ollama model variant
    (e.g. qwen3.5:9b-ctx16k has 16K baked in).
    """
    from crewai import LLM
    model_str = preset_data['models'][role]
    return LLM(model=model_str)


def load_crew(path: str) -> dict:
    """Load a crew YAML file and return the parsed dict."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def validate_crew(data: dict, preset_data: dict) -> None:
    """Raise ValueError if the crew dict is invalid.

    *preset_data* is the resolved preset dict (has a ``models`` key).
    """
    if not isinstance(data, dict):
        raise ValueError("Crew data must be a dict.")
    if 'agents' not in data:
        raise ValueError("Missing required top-level key: 'agents'")
    if 'tasks' not in data:
        raise ValueError("Missing required top-level key: 'tasks'")
    agents = data['agents']
    tasks = data['tasks']
    if not isinstance(agents, list):
        raise ValueError("'agents' must be a list.")
    if not isinstance(tasks, list):
        raise ValueError("'tasks' must be a list.")

    model_keys = set()
    if 'models' in preset_data:
        model_keys = set(preset_data['models'].keys())

    agent_names = set()
    for idx, agent in enumerate(agents):
        for field in ['name', 'role', 'goal', 'model']:
            if field not in agent:
                raise ValueError(
                    f"Agent at index {idx} missing required field: '{field}'"
                )
        # backstory is optional — default to role description
        if 'backstory' not in agent:
            agent['backstory'] = f"An expert {agent['role']}."
        # normalise tools: accept nested dicts, keep only string names
        if 'tools' in agent and isinstance(agent['tools'], list):
            normalised = []
            for t in agent['tools']:
                if isinstance(t, str):
                    normalised.append(t)
                elif isinstance(t, dict) and 'name' in t:
                    normalised.append(t['name'])
            agent['tools'] = normalised
        agent_names.add(agent['name'])
        model_key = agent['model']
        if model_keys and model_key not in model_keys:
            raise ValueError(
                f"Agent '{agent['name']}' references unknown model: '{model_key}'"
            )
    for idx, task in enumerate(tasks):
        for field in ['name', 'description', 'expected_output', 'agent']:
            if field not in task:
                raise ValueError(
                    f"Task at index {idx} missing required field: '{field}'"
                )
        if task['agent'] not in agent_names:
            raise ValueError(
                f"Task '{task['name']}' references unknown agent: '{task['agent']}'"
            )


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

def load_models(path: str, preset: Optional[str] = None) -> dict:
    """Legacy helper: load a YAML with presets, resolve one."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    if 'presets' not in data:
        return data

    presets = data['presets']
    if preset is None:
        preset = data.get('default_preset')
    if preset is None:
        preset = next(iter(presets))

    if preset not in presets:
        available = ', '.join(presets.keys())
        raise ValueError(f"Unknown preset '{preset}'. Available: {available}")

    return presets[preset]


def load_pipeline_config(path: Optional[str] = None) -> dict:
    """Legacy helper: load pipeline section from gat.yaml."""
    cfg = load_config(path) if path else _DEFAULT_CONFIG.copy()
    return {
        'requirements': cfg.get('requirements', {}),
        'execution': cfg.get('execution', {}),
        'timeouts': cfg.get('timeouts', {}),
        'tools': cfg.get('tools', {}),
    }
