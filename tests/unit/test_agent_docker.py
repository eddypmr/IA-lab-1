import io
import json
from typing import Any

from ai_agent_lab.config.settings import SandboxSettings, Settings
from ai_agent_lab.core.agent import Agent
from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.docker import register_docker_tools
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools


class CompletedDockerCli:
    def __init__(self, command: list[str], **kwargs: Any) -> None:
        self.command = command
        self.pid = 987654
        self.returncode = 0
        self.stdout = io.BytesIO(b"42\n")
        self.stderr = io.BytesIO(b"")

    def wait(self, timeout: float | None = None) -> int:
        return 0


class ModelRequestsCommand:
    def __init__(self) -> None:
        self.requests: list[list[dict[str, Any]]] = []
        self.responses = iter(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-python",
                            "function": {
                                "name": "execute_command",
                                "arguments": {"command": ["python", "-c", "print(40 + 2)"]},
                            },
                        }
                    ],
                },
                {"role": "assistant", "content": "El contenedor devolvió 42 con código 0."},
            ]
        )

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        self.requests.append(messages)
        return next(self.responses)


def test_agent_returns_container_result_to_model_as_observation(workspace: Workspace) -> None:
    model = ModelRequestsCommand()
    tools = register_default_tools(workspace)
    register_docker_tools(
        tools, DockerExecutor(workspace, SandboxSettings(), popen=CompletedDockerCli)
    )
    settings = Settings(workspace=workspace.root)
    answer = Agent(model, tools, settings).run("Ejecuta print(40 + 2) en Python.")

    observation = model.requests[1][-1]
    result = json.loads(observation["content"])
    assert answer == "El contenedor devolvió 42 con código 0."
    assert observation["role"] == "tool"
    assert observation["tool_name"] == "execute_command"
    assert observation["tool_call_id"] == "call-python"
    assert result["ok"] is True
    assert result["result"]["exit_code"] == 0
    assert result["result"]["stdout"] == "42\n"
