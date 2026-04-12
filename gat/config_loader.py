import yaml
from typing import Dict

def load_models(path: str) -> dict:
    """Load models.yaml and return the parsed dict."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_crew(path: str) -> dict:
    """Load a crew YAML file and return the parsed dict."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_crew(data: dict, models: dict) -> None:
    """Raise ValueError with a descriptive message if the crew dict is invalid."""
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
    agent_names = set()
    for idx, agent in enumerate(agents):
        for field in ['name', 'role', 'goal', 'backstory', 'model']:
            if field not in agent:
                raise ValueError(f"Agent at index {idx} missing required field: '{field}'")
        agent_names.add(agent['name'])
        model_key = agent['model']
        if 'models' not in models or model_key not in models['models']:
            raise ValueError(f"Agent '{agent['name']}' references unknown model: '{model_key}'")
    for idx, task in enumerate(tasks):
        for field in ['name', 'description', 'expected_output', 'agent']:
            if field not in task:
                raise ValueError(f"Task at index {idx} missing required field: '{field}'")
        if task['agent'] not in agent_names:
            raise ValueError(f"Task '{task['name']}' references unknown agent: '{task['agent']}'")
