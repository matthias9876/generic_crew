import sys
import pytest
from unittest import mock
from gat.cli import main


def test_requirements_dispatch(monkeypatch):
    m = mock.Mock(return_value="/run/requirements_reviewed.md")
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    main(["requirements", "--rd", "req.md"])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == "req.md"


def test_hire_dispatch(monkeypatch):
    m = mock.Mock(return_value="/run/crew.yaml")
    monkeypatch.setattr("gat.phases.hiring_phase.run", m)
    main(["hire", "--rd", "req.md"])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == "req.md"


def test_run_dispatch(monkeypatch):
    m = mock.Mock(return_value="done")
    monkeypatch.setattr("gat.phases.execution_phase.run", m)
    main(["run", "--rd", "req.md", "--crew", "crew.yaml"])
    m.assert_called_once()
    assert m.call_args.kwargs["rd_path"] == "req.md"
    assert m.call_args.kwargs["crew_yaml_path"] == "crew.yaml"


def test_run_dir_is_passed_through(tmp_path, monkeypatch):
    m = mock.Mock(return_value="/run/requirements_reviewed.md")
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    run_dir = str(tmp_path / "myrun")
    main(["--run-dir", run_dir, "requirements", "--rd", "req.md"])
    assert m.call_args.kwargs["run_dir"] == run_dir


def test_run_dir_is_auto_generated(tmp_path, monkeypatch):
    m = mock.Mock(return_value="/run/requirements_reviewed.md")
    monkeypatch.setattr("gat.phases.requirements_phase.run", m)
    monkeypatch.setattr("gat.config_loader.load_config", mock.Mock(return_value={}))
    monkeypatch.setattr("gat.config_loader.patch_ssl_for_unverified_instances", mock.Mock())
    monkeypatch.setattr("gat.config_loader.resolve_preset", mock.Mock(return_value={}))
    monkeypatch.chdir(tmp_path)
    main(["requirements", "--rd", "req.md"])
    run_dir = m.call_args.kwargs["run_dir"]
    assert "runs" in run_dir


def test_filenotfounderror(monkeypatch):
    def raise_fnf(*a, **kw):
        raise FileNotFoundError("not found")
    monkeypatch.setattr("gat.phases.requirements_phase.run", raise_fnf)
    with pytest.raises(SystemExit) as e:
        main(["requirements", "--rd", "req.md"])
    assert e.value.code == 1


def test_no_subcommand_exits():
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code != 0


def test_full_dispatch(monkeypatch):
    req_m = mock.Mock(return_value="/run/requirements_reviewed.md")
    hire_m = mock.Mock(return_value="/run/crew.yaml")
    exec_m = mock.Mock(return_value="done")
    monkeypatch.setattr("gat.phases.requirements_phase.run", req_m)
    monkeypatch.setattr("gat.phases.hiring_phase.run", hire_m)
    monkeypatch.setattr("gat.phases.execution_phase.run", exec_m)
    main(["full", "--rd", "req.md"])
    req_m.assert_called_once()
    hire_m.assert_called_once()
    exec_m.assert_called_once()
    # hire and execute should receive the reviewed requirements path
    assert hire_m.call_args.kwargs["rd_path"] == "/run/requirements_reviewed.md"
    assert exec_m.call_args.kwargs["rd_path"] == "/run/requirements_reviewed.md"
