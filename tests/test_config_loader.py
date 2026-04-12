import pytest
import os
import tempfile
import yaml
from gat.config_loader import load_models, load_crew, validate_crew

def test_load_models_happy_path(tmp_path):
    models_yaml = {'models': {'large': 'ollama/qwen3.5:35b-ctx32k'}}
    path = tmp_path / "models.yaml"
    with open(path, 'w') as f:
        yaml.dump(models_yaml, f)
    result = load_models(str(path))
    assert result['models']['large'] == 'ollama/qwen3.5:35b-ctx32k'

def test_load_models_missing_file():
    with pytest.raises(FileNotFoundError):
        load_models("/nonexistent/models.yaml")

def test_validate_crew_valid_data():
    models = {'models': {'large': 'foo'}}
    crew = {
        'agents': [{
            'name': 'Project Manager',
            'role': 'Project Manager',
            'goal': 'x',
            'backstory': 'y',
            'model': 'large',
            'tools': []
        }],
        'tasks': [{
            'name': 'plan',
            'description': 'desc',
            'expected_output': 'out',
            'agent': 'Project Manager'
        }]
    }
    validate_crew(crew, models)  # Should not raise

def test_validate_crew_missing_tasks_key():
    models = {'models': {'large': 'foo'}}
    crew = {'agents': []}
    with pytest.raises(ValueError) as e:
        validate_crew(crew, models)
    assert "tasks" in str(e.value)

def test_validate_crew_task_references_unknown_agent():
    models = {'models': {'large': 'foo'}}
    crew = {
        'agents': [{
            'name': 'Project Manager',
            'role': 'Project Manager',
            'goal': 'x',
            'backstory': 'y',
            'model': 'large',
            'tools': []
        }],
        'tasks': [{
            'name': 'plan',
            'description': 'desc',
            'expected_output': 'out',
            'agent': 'Unknown Agent'
        }]
    }
    with pytest.raises(ValueError) as e:
        validate_crew(crew, models)
    assert "unknown agent" in str(e.value)

def test_validate_crew_agent_references_unknown_model():
    models = {'models': {'large': 'foo'}}
    crew = {
        'agents': [{
            'name': 'Project Manager',
            'role': 'Project Manager',
            'goal': 'x',
            'backstory': 'y',
            'model': 'not_in_models',
            'tools': []
        }],
        'tasks': [{
            'name': 'plan',
            'description': 'desc',
            'expected_output': 'out',
            'agent': 'Project Manager'
        }]
    }
    with pytest.raises(ValueError) as e:
        validate_crew(crew, models)
    assert "unknown model" in str(e.value)

def test_load_crew_happy_path(tmp_path):
    crew_yaml = {
        'agents': [{
            'name': 'Project Manager',
            'role': 'Project Manager',
            'goal': 'x',
            'backstory': 'y',
            'model': 'large',
            'tools': []
        }],
        'tasks': [{
            'name': 'plan',
            'description': 'desc',
            'expected_output': 'out',
            'agent': 'Project Manager'
        }]
    }
    path = tmp_path / "crew.yaml"
    with open(path, 'w') as f:
        yaml.dump(crew_yaml, f)
    result = load_crew(str(path))
    assert 'agents' in result and 'tasks' in result
