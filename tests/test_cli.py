import sys
import pytest
from unittest import mock
from gat.cli import main

def test_requirements_dispatch(monkeypatch):
    m = mock.Mock(return_value="review.md")
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_models", lambda path, preset=None: {})
    main(["requirements", "--rd", "req.md"])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == "req.md"

def test_hire_dispatch(monkeypatch):
    m = mock.Mock(return_value="crew.yaml")
    monkeypatch.setattr("gat.phases.hiring_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_models", lambda path, preset=None: {})
    main(["hire", "--rd", "req.md"])
    m.assert_called_once()

def test_run_dispatch(monkeypatch):
    m = mock.Mock(return_value="done")
    monkeypatch.setattr("gat.phases.execution_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_models", lambda path, preset=None: {})
    main(["run", "--rd", "req.md", "--crew", "crew.yaml"])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == "req.md"
    assert m.call_args.kwargs["crew_yaml_path"] == "crew.yaml"

def test_requirements_default_output(monkeypatch):
    m = mock.Mock(return_value="review.md")
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_models", lambda path, preset=None: {})
    main(["requirements", "--rd", "req.md"])
    assert m.call_args.kwargs["output_path"] == "review.md"

def test_filenotfounderror(monkeypatch):
    def raise_fnf(path, preset=None):
        raise FileNotFoundError("not found")
    monkeypatch.setattr("gat.config_loader.load_models", raise_fnf)
    with pytest.raises(SystemExit) as e:
        main(["requirements", "--rd", "req.md"])
    assert e.value.code == 1

def test_no_subcommand_exits(monkeypatch):
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code != 0

def test_preset_flag_passed(monkeypatch):
    m = mock.Mock(return_value="review.md")
    load_m = mock.Mock(return_value={})
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_models", load_m)
    main(["requirements", "--rd", "req.md", "--preset", "gpu"])
    load_m.assert_called_once_with(mock.ANY, preset="gpu")
