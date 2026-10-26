import json
from copy import deepcopy
from typing import Any

import pytest

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.core.agent import Agent, IterationLimitError
from ai_agent_lab.llm.base import Message, ProviderError
from ai_agent_lab.tools.registry import ToolRegistry


class ScriptedProvider:
    def __init__(self, responses: list[Message | Exception]) -> None:
        self.responses = iter(responses)
        self.requests: list[list[Message]] = []

    def chat(self, messages: list[Message], tools: list[dict[str, Any]]) -> Message:
        self.requests.append(deepcopy(messages))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def tool_call(name: str = "doblar", arguments: object = None) -> Message:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "call-1", "function": {"name": name, "arguments": arguments or {"numero": 3}}}
        ],
    }


def test_conversation_history_and_reset(registry: ToolRegistry) -> None:
    provider = ScriptedProvider(
        [
            {"role": "assistant", "content": "Hola"},
            {"role": "assistant", "content": "Recuerdo"},
        ]
    )
    agent = Agent(provider, registry, Settings(system_prompt="Personalizado"))
    assert agent.run("hola") == "Hola"
    assert agent.run("¿qué dije?") == "Recuerdo"
    assert provider.requests[1][0]["content"] == "Personalizado"
    assert provider.requests[1][1]["content"] == "hola"
    agent.reset()
    assert agent.messages == [{"role": "system", "content": "Personalizado"}]


def test_tool_observation_is_returned_before_final_answer(registry: ToolRegistry) -> None:
    provider = ScriptedProvider([tool_call(), {"role": "assistant", "content": "6"}])
    agent = Agent(provider, registry, Settings())
    assert agent.run("dobla 3") == "6"
    observation = provider.requests[1][-1]
    assert observation["tool_name"] == "doblar"
    assert observation["tool_call_id"] == "call-1"
    assert json.loads(observation["content"]) == {"ok": True, "result": 6}


def test_model_can_correct_invalid_arguments(registry: ToolRegistry) -> None:
    provider = ScriptedProvider(
        [
            tool_call(arguments={"numero": "3"}),
            tool_call(arguments={"numero": 3}),
            {"role": "assistant", "content": "6"},
        ]
    )
    agent = Agent(provider, registry, Settings())
    assert agent.run("dobla 3") == "6"
    assert json.loads(provider.requests[1][-1]["content"])["ok"] is False
    assert json.loads(provider.requests[2][-1]["content"])["ok"] is True


def test_iteration_limit_preserves_real_observations(registry: ToolRegistry) -> None:
    provider = ScriptedProvider([tool_call(), {"role": "assistant", "content": "Fin"}])
    agent = Agent(provider, registry, Settings(max_iterations=1))
    with pytest.raises(IterationLimitError, match="límite"):
        agent.run("dobla")
    assert len(provider.requests) == 1
    assert any(message["role"] == "tool" for message in agent.messages)
    assert agent.run("continúa") == "Fin"


def test_tool_batch_limit_prevents_execution(registry: ToolRegistry) -> None:
    message = tool_call()
    message["tool_calls"] *= 2
    agent = Agent(ScriptedProvider([message]), registry, Settings(max_tool_calls_per_response=1))
    with pytest.raises(IterationLimitError, match="Demasiadas"):
        agent.run("hazlo")
    assert not any(message["role"] == "tool" for message in agent.messages)


def test_provider_error_after_tool_keeps_observations(registry: ToolRegistry) -> None:
    provider = ScriptedProvider([tool_call(), ProviderError("sin conexión")])
    agent = Agent(provider, registry, Settings())
    with pytest.raises(ProviderError, match="conexión"):
        agent.run("dobla")
    assert json.loads(agent.messages[-2]["content"])["result"] == 6
    assert "interrumpido" in agent.messages[-1]["content"]


def test_empty_prompt_never_calls_model(registry: ToolRegistry) -> None:
    provider = ScriptedProvider([])
    agent = Agent(provider, registry, Settings())
    with pytest.raises(ValueError):
        agent.run(" ")
    assert provider.requests == []
