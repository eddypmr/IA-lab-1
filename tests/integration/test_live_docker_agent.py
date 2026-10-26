"""Aceptación de Fase 2: Qwen genera el script y la herramienta lo ejecuta en Docker."""

import json
import os
from pathlib import Path

import pytest

from ai_agent_lab.config.settings import SandboxSettings, Settings
from ai_agent_lab.core.agent import Agent
from ai_agent_lab.llm.ollama_provider import OllamaProvider
from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.docker import register_docker_tools
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools

pytestmark = [
    pytest.mark.ollama,
    pytest.mark.docker,
    pytest.mark.acceptance,
    pytest.mark.skipif(
        os.environ.get("AI_AGENT_LAB_TEST_OLLAMA") != "1"
        or os.environ.get("AI_AGENT_LAB_TEST_DOCKER") != "1",
        reason="Requiere AI_AGENT_LAB_TEST_OLLAMA=1 y AI_AGENT_LAB_TEST_DOCKER=1.",
    ),
]


def test_qwen_generates_and_executes_python_inside_docker(tmp_path: Path) -> None:
    settings = Settings(
        host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        model=os.environ.get("OLLAMA_MODEL", "qwen3:4b"),
        workspace=tmp_path,
        sandbox=SandboxSettings(timeout_seconds=15),
    )
    workspace = Workspace(tmp_path)
    executor = DockerExecutor(workspace, settings.sandbox)
    with OllamaProvider(settings) as provider:
        provider.check()
        executor.check()
        tools = register_default_tools(workspace)
        register_docker_tools(tools, executor)
        agent = Agent(provider, tools, settings)
        answer = agent.run(
            "Crea sum.py con un programa Python que calcule 19 + 23 e imprima el resultado. "
            "Después ejecútalo usando execute_python con ruta sum.py. Indica el código de "
            "salida y stdout reales del contenedor."
        )

    assert (tmp_path / "sum.py").is_file()
    assert "42" in answer
    results = [
        json.loads(message["content"])
        for message in agent.messages
        if message.get("role") == "tool" and message.get("tool_name") == "execute_python"
    ]
    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0]["result"]["exit_code"] == 0
    assert "42" in results[0]["result"]["stdout"]
