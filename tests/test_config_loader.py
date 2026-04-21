import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock
from gat.config_loader import load_models, load_crew, validate_crew, make_llm, _resolve_instance

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


# ---------------------------------------------------------------------------
# _resolve_instance
# ---------------------------------------------------------------------------

def _cfg_with_instances(instances, default='local'):
    return {'ollama_instances': instances, 'default_instance': default}


def test_resolve_instance_default():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    inst = _resolve_instance(cfg, None)
    assert inst['host'] == 'localhost'
    assert inst['port'] == 11434


def test_resolve_instance_named():
    cfg = _cfg_with_instances({
        'local': {'host': 'localhost', 'port': 11434},
        'remote': {'host': '10.17.90.127', 'port': 8443, 'username': 'admin', 'password': 'secret'},
    })
    inst = _resolve_instance(cfg, 'remote')
    assert inst['host'] == '10.17.90.127'
    assert inst['port'] == 8443
    assert inst['username'] == 'admin'


def test_resolve_instance_unknown_raises():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    with pytest.raises(ValueError, match="Unknown Ollama instance 'ghost'"):
        _resolve_instance(cfg, 'ghost')


# ---------------------------------------------------------------------------
# make_llm — instance resolution and auth header injection
# ---------------------------------------------------------------------------

def _make_preset(model_str='ollama/test:latest', instance_override=None):
    preset = {'models': {'coder': model_str}}
    if instance_override:
        preset['instances'] = {'coder': instance_override}
    return preset


def test_make_llm_no_auth_sets_base_url():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    preset = _make_preset()
    with patch('gat.config_loader._ensure_ollama_model_available') as mock_ensure, \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        make_llm(preset, 'coder', config=cfg)
        call_kwargs = MockLLM.call_args[1]
        assert call_kwargs['base_url'] == 'http://localhost:11434'
        assert 'extra_headers' not in call_kwargs
        mock_ensure.assert_called_once()


def test_make_llm_with_auth_sets_authorization_header():
    cfg = _cfg_with_instances({
        'remote': {'host': '10.17.90.127', 'port': 8443,
                   'username': 'admin', 'password': 'aF7t'},
    }, default='remote')
    preset = _make_preset()
    with patch('gat.config_loader._ensure_ollama_model_available') as mock_ensure, \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        make_llm(preset, 'coder', config=cfg)
        call_kwargs = MockLLM.call_args[1]
        assert call_kwargs['base_url'] == 'http://10.17.90.127:8443'
        auth = call_kwargs['extra_headers']['Authorization']
        assert auth.startswith('Basic ')
        import base64
        decoded = base64.b64decode(auth.split(' ', 1)[1]).decode()
        assert decoded == 'admin:aF7t'
        mock_ensure.assert_called_once()


def test_make_llm_per_role_instance_override():
    cfg = _cfg_with_instances({
        'local': {'host': 'localhost', 'port': 11434},
        'gpu_box': {'host': '192.168.1.10', 'port': 11434},
    })
    preset = _make_preset(instance_override='gpu_box')
    with patch('gat.config_loader._ensure_ollama_model_available') as mock_ensure, \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        make_llm(preset, 'coder', config=cfg)
        call_kwargs = MockLLM.call_args[1]
        assert 'gpu_box' in call_kwargs['base_url'] or '192.168.1.10' in call_kwargs['base_url']
        mock_ensure.assert_called_once()


def test_make_llm_does_not_pull_when_model_exists():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    preset = _make_preset(model_str='ollama/qwen2.5-coder:7b')

    tags_response = MagicMock()
    tags_response.json.return_value = {'models': [{'name': 'qwen2.5-coder:7b'}]}
    tags_response.raise_for_status.return_value = None

    with patch('gat.config_loader.httpx.get', return_value=tags_response) as mock_get, \
         patch('gat.config_loader.httpx.post') as mock_post, \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        make_llm(preset, 'coder', config=cfg)
        mock_get.assert_called_once()
        mock_post.assert_not_called()


def test_make_llm_pulls_when_model_missing():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    preset = _make_preset(model_str='ollama/qwen2.5-coder:7b')

    tags_response = MagicMock()
    tags_response.json.return_value = {'models': [{'name': 'other-model:latest'}]}
    tags_response.raise_for_status.return_value = None
    pull_response = MagicMock()
    pull_response.raise_for_status.return_value = None

    with patch('gat.config_loader.httpx.get', return_value=tags_response), \
         patch('gat.config_loader.httpx.post', return_value=pull_response) as mock_post, \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        make_llm(preset, 'coder', config=cfg)
        mock_post.assert_called_once()
        call = mock_post.call_args
        assert call[0][0] == 'http://localhost:11434/api/pull'
        assert call[1]['json'] == {'name': 'qwen2.5-coder:7b', 'stream': False}


def test_make_llm_raises_clear_error_when_ollama_unreachable():
    cfg = _cfg_with_instances({'local': {'host': 'localhost', 'port': 11434}})
    preset = _make_preset(model_str='ollama/qwen2.5-coder:7b')

    with patch('gat.config_loader.httpx.get', side_effect=Exception("boom")), \
         patch('crewai.LLM') as MockLLM:
        MockLLM.return_value = MagicMock()
        with pytest.raises(RuntimeError, match="Failed to query Ollama models"):
            make_llm(preset, 'coder', config=cfg)
