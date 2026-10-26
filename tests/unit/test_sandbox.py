import io
import subprocess
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_agent_lab.config.settings import SandboxSettings
from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools
from ai_agent_lab.tools.registry import ToolError


def executor_for(workspace: Workspace, **kwargs: object) -> DockerExecutor:
    return DockerExecutor(workspace, SandboxSettings(), **kwargs)


def test_docker_argv_contains_workspace_and_isolation_flags(workspace: Workspace) -> None:
    executor = executor_for(workspace)
    argv = executor._build_argv("ai-agent-lab-test", ["python", "-c", "print(1)"])
    for option in (
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--cpus",
        "--memory",
        "--memory-swap",
        "--pids-limit",
        "--tmpfs",
        "--user",
        "--mount",
    ):
        assert option in argv
    assert f"type=bind,source={workspace.root},target=/workspace" in argv
    assert "-v" not in argv and "/var/run/docker.sock" not in argv
    assert argv[-3:] == ["python", "-c", "print(1)"]


@pytest.mark.parametrize("command", [[], ["sh", "-c", ""], ["python", "\x00"]])
def test_rejects_invalid_command_before_starting_docker(
    workspace: Workspace, command: list[str]
) -> None:
    def never_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("Docker no debe iniciarse para argumentos inválidos")

    with pytest.raises(ToolError):
        executor_for(workspace, popen=never_called).execute(command)


class FakeProcess:
    pid = 987654

    def __init__(self, code: int, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = code
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.command: list[str] | None = None
        self.kwargs: dict[str, object] = {}

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


def make_popen_process(
    code: int = 0, stdout: bytes = b"answer\n", stderr: bytes = b""
) -> Callable[..., FakeProcess]:
    def popen(command: list[str], **kwargs: object) -> FakeProcess:
        process = FakeProcess(code, stdout, stderr)
        process.command = command
        process.kwargs = kwargs
        captured.append(process)
        return process

    captured: list[FakeProcess] = []
    popen.captured = captured  # type: ignore[attr-defined]
    return popen


def test_execute_returns_real_exit_code_and_bounded_output(workspace: Workspace) -> None:
    popen = make_popen_process(7, b"result\n", b"boom\n")
    executor = executor_for(workspace, popen=popen)
    result = executor.execute(["python", "-c", "print(1)"])
    assert result["exit_code"] == 7
    assert result["stdout"] == "result\n"
    assert result["stderr"] == "boom\n"
    assert result["timed_out"] is False
    process = popen.captured[0]  # type: ignore[attr-defined]
    assert process.kwargs["shell"] is False
    assert process.kwargs["stdin"] == subprocess.DEVNULL
    assert "python" not in process.command[0]
    assert process.command[-3:] == ["python", "-c", "print(1)"]


def test_output_is_capped_while_streams_are_drained(workspace: Workspace) -> None:
    popen = make_popen_process(stdout=b"x" * 1500)
    settings = SandboxSettings(output_limit_bytes=1024)
    result = DockerExecutor(workspace, settings, popen=popen).execute(["python", "-c", "pass"])
    assert len(result["stdout"]) == 1024
    assert result["output_truncated"] is True


def test_timeout_stops_named_container_and_reports_exit_124(workspace: Workspace) -> None:
    class TimedProcess(FakeProcess):
        def __init__(self) -> None:
            super().__init__(0)
            self.waits = 0

        def wait(self, timeout: float | None = None) -> int:
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("docker run", timeout)
            return 0

    process = TimedProcess()
    calls: list[list[str]] = []

    def popen(command: list[str], **kwargs: object) -> TimedProcess:
        process.command = command
        process.kwargs = kwargs
        return process

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="")

    result = DockerExecutor(workspace, SandboxSettings(), popen=popen, run=run).execute(
        ["python", "-c", "while True: pass"]
    )
    assert result["exit_code"] == 124 and result["timed_out"] is True
    assert calls[0][1:4] == ["stop", "--time", "2"]
    assert calls[0][-1] == process.command[process.command.index("--name") + 1]


def test_timeout_falls_back_to_kill_if_stop_fails(workspace: Workspace) -> None:
    class TimedProcess(FakeProcess):
        def __init__(self) -> None:
            super().__init__(0)
            self.waits = 0

        def wait(self, timeout: float | None = None) -> int:
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("docker run", timeout)
            return 0

    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(returncode=1, stdout="")

    executor_for(workspace, popen=lambda *args, **kwargs: TimedProcess(), run=run).execute(
        ["python", "-c", "pass"]
    )
    assert calls[1][1] == "kill"


def test_timeout_falls_back_to_kill_if_stop_times_out(workspace: Workspace) -> None:
    class TimedProcess(FakeProcess):
        def __init__(self) -> None:
            super().__init__(0)
            self.waits = 0

        def wait(self, timeout: float | None = None) -> int:
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("docker run", timeout)
            return 0

    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append(command)
        if command[1] == "stop":
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))
        return SimpleNamespace(returncode=0, stdout="")

    executor_for(workspace, popen=lambda *args, **kwargs: TimedProcess(), run=run).execute(
        ["python", "-c", "pass"]
    )
    assert [command[1] for command in calls] == ["stop", "kill"]


def test_python_script_requires_existing_relative_utf8_file(workspace: Workspace) -> None:
    executor = executor_for(workspace, popen=make_popen_process())
    (workspace.root / "tools").mkdir()
    workspace.crear_archivo("tools/demo.py", "print('ok')")
    result = executor.execute_python("tools/demo.py", ["arg with spaces"])
    assert result["stdout"] == "answer\n"
    process = executor._popen.captured[0]  # type: ignore[attr-defined]
    assert process.command[-3:] == ["python", "/workspace/tools/demo.py", "arg with spaces"]


@pytest.mark.parametrize("ruta", ["../outside.py", "missing.py", "link.py", "note.txt"])
def test_python_tool_rejects_unsafe_missing_or_non_python_paths(
    workspace: Workspace, tmp_path: Path, ruta: str
) -> None:
    (tmp_path / "secret.py").write_text("pass", encoding="utf-8")
    if ruta == "link.py":
        (workspace.root / ruta).symlink_to(tmp_path / "secret.py")
    executor = executor_for(workspace, popen=make_popen_process())
    with pytest.raises(ToolError):
        executor.execute_python(ruta)


def test_registers_only_two_docker_capabilities(workspace: Workspace) -> None:
    from ai_agent_lab.tools.docker import register_docker_tools

    registry = register_default_tools(workspace)
    register_docker_tools(registry, executor_for(workspace))
    names = {tool["function"]["name"] for tool in registry.schemas()}
    assert names == {
        "obtener_fecha",
        "listar_archivos",
        "leer_archivo",
        "crear_archivo",
        "execute_command",
        "execute_python",
    }


def test_check_rejects_remote_daemon_and_never_pulls_images(workspace: Workspace) -> None:
    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout='"ssh://remote/docker"\n', stderr="")

    with pytest.raises(ToolError, match="endpoints Docker locales"):
        DockerExecutor(workspace, SandboxSettings(), run=run).check()


def test_check_accepts_local_linux_daemon_and_preloaded_image(workspace: Workspace) -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        commands.append(command)
        if "context" in command:
            return SimpleNamespace(
                returncode=0, stdout='"unix:///var/run/docker.sock"\n', stderr=""
            )
        if "info" in command:
            return SimpleNamespace(returncode=0, stdout="linux 29.1.3\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="sha256:0123456789\n", stderr="")

    result = DockerExecutor(workspace, SandboxSettings(), run=run).check()
    assert result == {
        "server": "29.1.3",
        "endpoint": "unix:///var/run/docker.sock",
        "image": "python:3.10-slim",
    }
    assert len(commands) == 3
    assert all(command[1] != "pull" for command in commands)


@pytest.mark.parametrize(
    ("phase", "stdout", "stderr", "message"),
    [
        ("context", "", "", "Docker Context"),
        ("daemon", "", "pipe cerrado", "Docker daemon no disponible"),
        ("image", "", "", "no está descargada"),
    ],
)
def test_check_describes_missing_docker_prerequisites(
    workspace: Workspace, phase: str, stdout: str, stderr: str, message: str
) -> None:
    def run(command: list[str], **kwargs: object) -> SimpleNamespace:
        if phase == "context" or phase == "daemon" and "info" in command:
            return SimpleNamespace(returncode=1, stdout=stdout, stderr=stderr)
        if phase == "daemon":
            return SimpleNamespace(returncode=0, stdout='"unix:///var/run/docker.sock"', stderr="")
        if "context" in command:
            return SimpleNamespace(returncode=0, stdout='"unix:///var/run/docker.sock"', stderr="")
        if "info" in command:
            return SimpleNamespace(returncode=0, stdout="linux 29.1.3", stderr="")
        return SimpleNamespace(returncode=1, stdout=stdout, stderr=stderr)

    with pytest.raises(ToolError, match=message):
        DockerExecutor(workspace, SandboxSettings(), run=run).check()
