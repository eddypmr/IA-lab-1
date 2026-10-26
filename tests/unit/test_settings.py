import json
from pathlib import Path

import pytest

from ai_agent_lab.config.settings import SandboxSettings, Settings, load_settings


def test_defaults_support_wsl_python_and_small_gpu() -> None:
    settings = load_settings()
    assert settings.model == "qwen3:4b"
    assert settings.num_ctx == 8192
    assert settings.think is True
    assert settings.num_predict == 4096


def test_config_resolves_workspace_relative_to_config(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"workspace": "files", "num_ctx": 2048}), encoding="utf-8")
    settings = load_settings(config)
    assert settings.workspace == tmp_path / "files"
    assert settings.num_ctx == 2048


def test_sandbox_config_resolves_and_validates_limits(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"sandbox": {"timeout_seconds": 45, "memory_mb": 1024, "cpus": 2}}),
        encoding="utf-8",
    )
    settings = load_settings(config)
    assert settings.sandbox.timeout_seconds == 45
    assert settings.sandbox.memory_mb == 1024
    assert settings.sandbox.cpus == 2


@pytest.mark.parametrize(
    "data",
    [[], {"modle": "oops"}, {"workspace": 42}, {"workspace": ""}, {"think": "false"}],
)
def test_rejects_invalid_config(tmp_path: Path, data: object) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(config)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("max_iterations", 0),
        ("max_iterations", True),
        ("max_tool_calls_per_response", -1),
        ("num_ctx", "4096"),
        ("num_predict", 0),
        ("top_k", True),
        ("top_p", 0),
        ("top_p", 1.1),
        ("timeout_seconds", 0),
        ("timeout_seconds", float("inf")),
        ("temperature", float("nan")),
        ("temperature", 3),
        ("think", 1),
        ("model", " "),
        ("system_prompt", ""),
        ("host", "file:///tmp/ollama"),
        ("host", "http://user:secret@localhost:11434"),
        ("host", "http://localhost:11434/api"),
        ("host", "http://localhost:bad"),
    ],
)
def test_rejects_invalid_settings(key: str, value: object) -> None:
    with pytest.raises(ValueError):
        Settings(**{key: value})


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("image", "--privileged"),
        ("image", "python;cat /etc/passwd"),
        ("timeout_seconds", 301),
        ("timeout_seconds", 0),
        ("memory_mb", 32),
        ("memory_mb", 16384),
        ("memory_mb", True),
        ("cpus", 0),
        ("cpus", 5),
        ("pids_limit", 1),
        ("tmpfs_size_mb", 513),
        ("output_limit_bytes", 512),
    ],
)
def test_rejects_invalid_sandbox_settings(key: str, value: object) -> None:
    with pytest.raises(ValueError):
        SandboxSettings(**{key: value})


@pytest.mark.parametrize(
    "data",
    [{"sandbox": []}, {"sandbox": {"no_such_option": 1}}],
)
def test_rejects_malformed_sandbox_config(tmp_path: Path, data: object) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="sandbox"):
        load_settings(config)
