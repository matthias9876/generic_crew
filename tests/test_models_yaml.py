import yaml
import pytest
from gat.config_loader import load_models

MODELS_PATH = "gat/models.yaml"

def test_yaml_valid():
    with open(MODELS_PATH) as f:
        yaml.safe_load(f)

def test_presets_key():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    assert "presets" in parsed

def test_gpu_preset_aliases():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for alias in ["large", "dev", "tester"]:
        assert alias in parsed["presets"]["gpu"]["models"]

def test_precise_preset_aliases():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for alias in ["large", "dev", "tester"]:
        assert alias in parsed["presets"]["precise"]["models"]

def test_values_non_empty_strings():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for preset in parsed["presets"].values():
        for v in preset["models"].values():
            assert isinstance(v, str) and v.strip()

def test_ollama_prefix():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for preset in parsed["presets"].values():
        for v in preset["models"].values():
            assert v.startswith("ollama/")

def test_load_models_gpu_preset():
    result = load_models(MODELS_PATH, preset="gpu")
    assert "models" in result
    assert result["models"]["large"] == "ollama/qwen3.5:9b-ctx16k"

def test_load_models_precise_preset():
    result = load_models(MODELS_PATH, preset="precise")
    assert "models" in result
    assert result["models"]["large"] == "ollama/qwen3.5:35b-ctx32k"

def test_load_models_default_preset():
    result = load_models(MODELS_PATH)
    assert "models" in result

def test_load_models_unknown_preset():
    with pytest.raises(ValueError, match="Unknown preset"):
        load_models(MODELS_PATH, preset="nonexistent")
