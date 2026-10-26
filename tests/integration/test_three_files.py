"""Aceptación determinista: componentes reales y HTTP Ollama simulado, sin GPU."""

import json
from pathlib import Path

import httpx

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.core.agent import Agent
from ai_agent_lab.llm.ollama_provider import OllamaProvider
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools


def test_creates_three_files_and_checks_them_through_tools(tmp_path: Path) -> None:
    expected = {"python.txt": "Python", "docker.txt": "Docker", "cuda.txt": "CUDA"}
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 1:
            assert len(payload["tools"]) == 4
            calls = [
                {
                    "function": {
                        "name": "crear_archivo",
                        "arguments": {"ruta": name, "contenido": text},
                    }
                }
                for name, text in expected.items()
            ]
        elif len(requests) == 2:
            observations = [m for m in payload["messages"] if m["role"] == "tool"]
            assert len(observations) == 3
            assert all(json.loads(m["content"])["ok"] for m in observations)
            calls = [{"function": {"name": "listar_archivos", "arguments": {}}}] + [
                {"function": {"name": "leer_archivo", "arguments": {"ruta": name}}}
                for name in expected
            ]
        else:
            observations = [m for m in payload["messages"] if m["role"] == "tool"]
            listing = json.loads(observations[3]["content"])
            assert listing["result"]["archivos"] == sorted(expected)
            for observation, text in zip(observations[4:], expected.values(), strict=True):
                assert json.loads(observation["content"])["result"]["contenido"] == text
            return httpx.Response(
                200,
                json={
                    "done": True,
                    "message": {"role": "assistant", "content": "Tres archivos comprobados."},
                },
            )
        return httpx.Response(
            200,
            json={
                "done": True,
                "message": {"role": "assistant", "content": "", "tool_calls": calls},
            },
        )

    settings = Settings(workspace=tmp_path)
    with httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(settings, client=client)
        agent = Agent(provider, register_default_tools(Workspace(tmp_path)), settings)
        assert agent.run("Crea y comprueba tres archivos.") == "Tres archivos comprobados."
    assert len(requests) == 3
    assert {name: (tmp_path / name).read_text(encoding="utf-8") for name in expected} == expected
