from pathlib import Path

import pytest

from ai_agent_lab import main as cli
from ai_agent_lab.llm.base import ProviderError


class FakeProvider:
    def __init__(self, settings: object) -> None:
        pass

    def __enter__(self) -> "FakeProvider":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def chat(self, messages: object, tools: object) -> dict[str, str]:
        return {"role": "assistant", "content": "Respuesta de prueba"}

    def check(self) -> dict[str, str]:
        return {"version": "0.14.11", "model": "qwen3:4b"}


def test_prompt_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)
    assert cli.main(["--workspace", str(tmp_path), "--prompt", "hola"]) == 0
    assert "Respuesta de prueba" in capsys.readouterr().out


def test_check_does_not_create_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class ReadySandbox:
        def __init__(self, workspace: object, settings: object) -> None:
            pass

        def check(self) -> dict[str, str]:
            return {
                "server": "29.1.3",
                "endpoint": "unix:///var/run/docker.sock",
                "image": "python:3.10-slim",
            }

    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)
    monkeypatch.setattr(cli, "DockerExecutor", ReadySandbox)
    root = tmp_path / "not-created"
    assert cli.main(["--check", "--workspace", str(root)]) == 0
    assert not root.exists()


def test_interactive_reset_and_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)
    inputs = iter(["", "hola", "/reset", "/salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    assert cli.main(["--workspace", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Respuesta de prueba" in output and "Historial reiniciado" in output


def test_eof_exits_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)

    def eof(prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert cli.main(["--workspace", str(tmp_path)]) == 0


def test_ctrl_c_returns_130(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "OllamaProvider", FakeProvider)

    def cancel(prompt: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", cancel)
    assert cli.main(["--workspace", str(tmp_path)]) == 130


def test_connection_error_has_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class BrokenProvider(FakeProvider):
        def chat(self, messages: object, tools: object) -> dict[str, str]:
            raise ProviderError("sin conexión")

    monkeypatch.setattr(cli, "OllamaProvider", BrokenProvider)
    assert cli.main(["--workspace", str(tmp_path), "--prompt", "hola"]) == 1
    assert "sin conexión" in capsys.readouterr().err


def test_cli_overrides_config_and_loads_system_prompt(tmp_path: Path) -> None:
    config = tmp_path / "settings.json"
    config.write_text('{"model": "otro", "num_ctx": 2048}', encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Responde brevemente.", encoding="utf-8")
    args = cli.build_parser().parse_args(
        ["--config", str(config), "--model", "qwen3:4b", "--system-prompt-file", str(prompt)]
    )
    settings = cli.settings_from_args(args)
    assert settings.model == "qwen3:4b"
    assert settings.num_ctx == 2048
    assert settings.system_prompt == "Responde brevemente."
