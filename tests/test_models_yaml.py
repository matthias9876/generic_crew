import yaml
import pytest

MODELS_PATH = "gat/models.yaml"

# Test 1 — File is valid YAML
def test_yaml_valid():
    with open(MODELS_PATH) as f:
        yaml.safe_load(f)

# Test 2 — Top-level key exists
def test_top_level_key():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    assert "models" in parsed

# Test 3 — Known aliases present
def test_known_aliases_present():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for alias in ["large", "dev", "tester"]:
        assert alias in parsed["models"]

# Test 4 — Values are non-empty strings
def test_values_non_empty_strings():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for v in parsed["models"].values():
        assert isinstance(v, str) and v.strip()

# Test 5 — Ollama prefix
def test_ollama_prefix():
    with open(MODELS_PATH) as f:
        parsed = yaml.safe_load(f)
    for v in parsed["models"].values():
        assert v.startswith("ollama/")
