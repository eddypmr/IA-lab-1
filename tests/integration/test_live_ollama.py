"""Prueba real explícita: usa el modelo local y archivos temporales de Pytest."""

import json
import os
from pathlib import Path

import pytest

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.core.agent import Agent
from ai_agent_lab.llm.ollama_provider import OllamaProvider
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools

pytestmark = [
    pytest.mark.ollama,
    pytest.mark.skipif(
        os.environ.get("AI_AGENT_LAB_TEST_OLLAMA") != "1",
        reason="Activar explícitamente con AI_AGENT_LAB_TEST_OLLAMA=1.",
    ),
]


def test_qwen_creates_lists_and_reads_three_files(tmp_path: Path) -> None:
    settings = Settings(
        host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        model=os.environ.get("OLLAMA_MODEL", "qwen3:4b"),
        workspace=tmp_path,
    )
    with OllamaProvider(settings) as provider:
        provider.check()
        agent = Agent(provider, register_default_tools(Workspace(tmp_path)), settings)
        answer = agent.run(
            "Crea exactamente tres archivos nuevos en el workspace: python.txt con contenido "
            "'Python es un lenguaje.', docker.txt con 'Docker usa contenedores.' y cuda.txt con "
            "'CUDA permite usar la GPU.'. Después llama a listar_archivos y a leer_archivo "
            "para cada uno de los tres archivos. No termines antes de comprobar sus contenidos."
        )
    assert answer.strip()
    for name, subject in {
        "python.txt": "Python",
        "docker.txt": "Docker",
        "cuda.txt": "CUDA",
    }.items():
        assert subject in (tmp_path / name).read_text(encoding="utf-8")
    observations = [
        (message["tool_name"], json.loads(message["content"]))
        for message in agent.messages
        if message["role"] == "tool"
    ]
    successful = [(name, result["result"]) for name, result in observations if result["ok"]]
    created = {result["ruta"] for name, result in successful if name == "crear_archivo"}
    read = {result["ruta"] for name, result in successful if name == "leer_archivo"}
    assert created == read == {"python.txt", "docker.txt", "cuda.txt"}
    assert any(
        name == "listar_archivos" and set(result["archivos"]) == created
        for name, result in successful
    )
