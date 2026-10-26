"""Docker real y opcional. No descarga imágenes ni crea recursos en el host."""

import os

import pytest

from ai_agent_lab.config.settings import SandboxSettings
from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.filesystem import Workspace

pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(
        os.environ.get("AI_AGENT_LAB_TEST_DOCKER") != "1",
        reason="Activar explícitamente con AI_AGENT_LAB_TEST_DOCKER=1.",
    ),
]


def test_executes_python_script_in_unprivileged_offline_container(tmp_path) -> None:
    workspace = Workspace(tmp_path / "workspace")
    (workspace.root / "demo.py").write_text(
        "import os\nfrom pathlib import Path\n"
        "Path('result.txt').write_text('salida del contenedor', encoding='utf-8')\n"
        "print(f'uid={os.getuid()}')\nprint('script=ok')\n",
        encoding="utf-8",
    )
    executor = DockerExecutor(workspace, SandboxSettings())
    report = executor.check()
    result = executor.execute_python("demo.py")

    assert report["image"] == "python:3.10-slim"
    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert f"uid={os.getuid()}" in result["stdout"]
    assert "script=ok" in result["stdout"]
    assert (workspace.root / "result.txt").read_text(encoding="utf-8") == "salida del contenedor"


def test_script_cannot_reach_network_or_write_to_container_root(tmp_path) -> None:
    workspace = Workspace(tmp_path / "workspace")
    (workspace.root / "limits.py").write_text(
        "from pathlib import Path\nimport socket\n"
        "try:\n Path('/etc/agent-lab-write-test').write_text('bad')\n"
        "except OSError:\n print('root=read-only')\n"
        "try:\n socket.create_connection(('1.1.1.1', 80), timeout=2)\n"
        " print('network=available')\n"
        "except OSError:\n print('network=disabled')\n",
        encoding="utf-8",
    )
    result = DockerExecutor(workspace, SandboxSettings()).execute_python("limits.py")
    assert result["exit_code"] == 0
    assert "root=read-only" in result["stdout"]
    assert "network=disabled" in result["stdout"]
