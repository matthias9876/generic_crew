import base64
import os
import yaml
import httpx
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Built-in defaults (same values as the shipped gat/gat.yaml).
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG = {
    'ollama_instances': {
        'local': {'host': 'localhost', 'port': 11434},
    },
    'default_instance': 'local',
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

def load_config(paths) -> dict:
    """Load one or more YAML config files and merge with built-in defaults.

    *paths* can be a single path string or a list of paths.  Files are
    deep-merged onto the defaults first, then each subsequent file is
    **shallow-merged** (top-level keys overwrite) onto the result so
    that later files override earlier ones.
    """
    if isinstance(paths, str):
        paths = [paths]

    cfg = _DEFAULT_CONFIG.copy()
    first = True
    for p in paths:
        if p and os.path.isfile(p):
            with open(p, 'r') as f:
                user_cfg = yaml.safe_load(f) or {}
            if first:
                cfg = _deep_merge(cfg, user_cfg)
                first = False
            else:
                cfg.update(user_cfg)
    return cfg


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


def _resolve_instance(config: dict, instance_name: Optional[str]) -> dict:
    """Return the instance dict for *instance_name* (or the default).

    Raises ValueError if the name is unknown.
    """
    instances = config.get('ollama_instances', _DEFAULT_CONFIG['ollama_instances'])
    if not instance_name:
        instance_name = config.get('default_instance', 'local')
    if instance_name not in instances:
        available = ', '.join(instances.keys())
        raise ValueError(
            f"Unknown Ollama instance '{instance_name}'. Available: {available}"
        )
    return instances[instance_name]


def _ensure_ollama_model_available(model_str: str, base_url: str, extra_headers: Optional[dict] = None) -> None:
    """Ensure the Ollama model exists on the target instance; pull if missing."""
    if not model_str.startswith("ollama/"):
        return

    model_name = model_str.split("/", 1)[1]
    headers = extra_headers or {}

    tags_resp = httpx.get(f"{base_url}/api/tags", headers=headers, timeout=30.0)
    tags_resp.raise_for_status()
    tags_payload = tags_resp.json() or {}
    available = {
        item.get("name") or item.get("model")
        for item in tags_payload.get("models", [])
        if isinstance(item, dict)
    }
    if model_name in available:
        return

    pull_resp = httpx.post(
        f"{base_url}/api/pull",
        headers=headers,
        json={"name": model_name, "stream": False},
        timeout=300.0,
    )
    pull_resp.raise_for_status()


def make_llm(preset_data: dict, role: str, config: Optional[dict] = None):
    """Create a CrewAI LLM for the given role.

    Resolves the Ollama instance (base_url + optional Basic-Auth headers)
    from *config*.  If *config* is omitted the built-in defaults are used
    (localhost:11434, no auth).

    Per-role instance override: add an ``instances`` key to the preset::

        gpu:
          models:
            coder: "ollama/qwen2.5-coder:7b"
          instances:          # optional – overrides default_instance per role
            coder: workstation

    Context window size is controlled by the Ollama model variant
    (e.g. qwen3.5:9b-ctx16k has 16K baked in).
    """
    from crewai import LLM

    model_str = preset_data['models'][role]

    # Determine which Ollama instance serves this role.
    instance_name = (preset_data.get('instances') or {}).get(role)
    resolved_config = config or _DEFAULT_CONFIG
    instance = _resolve_instance(resolved_config, instance_name)

    host = instance['host']
    port = instance['port']
    scheme = instance.get('scheme', 'http')
    base_url = f"{scheme}://{host}:{port}"

    extra_headers = {}
    if instance.get('username') and instance.get('password'):
        credentials = f"{instance['username']}:{instance['password']}"
        token = base64.b64encode(credentials.encode()).decode()
        extra_headers['Authorization'] = f"Basic {token}"

    kwargs = {'model': model_str, 'base_url': base_url}
    if extra_headers:
        kwargs['extra_headers'] = extra_headers

    _ensure_ollama_model_available(model_str, base_url, extra_headers=extra_headers)

    return LLM(**kwargs)


def patch_ssl_for_unverified_instances(config: dict) -> None:
    """Monkey-patch httpx to disable SSL verification globally.

    Called once at startup when any configured Ollama instance has
    ``ssl_verify: false``.  This is necessary because the OpenAI SDK
    constructs its own httpx clients internally and there is no per-request
    hook to override SSL verification.
    """
    instances = config.get('ollama_instances', {})
    if not any(inst.get('ssl_verify') is False for inst in instances.values()):
        return

    import ssl
    import httpx

    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]

    _orig_client = httpx.Client.__init__
    def _patched_client(self, *args, **kwargs):
        kwargs.setdefault('verify', False)
        _orig_client(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_client  # type: ignore[method-assign]

    _orig_async = httpx.AsyncClient.__init__
    def _patched_async(self, *args, **kwargs):
        kwargs.setdefault('verify', False)
        _orig_async(self, *args, **kwargs)
    httpx.AsyncClient.__init__ = _patched_async  # type: ignore[method-assign]


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
