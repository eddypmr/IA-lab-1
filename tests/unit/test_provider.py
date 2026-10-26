import json
from collections.abc import Callable

import httpx
import pytest

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.llm.base import ProviderError
from ai_agent_lab.llm.ollama_provider import OllamaProvider


def response(message: object) -> dict[str, object]:
    return {"done": True, "message": message}


def provider_for(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaProvider:
    client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler))
    return OllamaProvider(Settings(), client=client)


def test_uses_native_ollama_payload_and_preserves_thinking() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3:4b"
        assert payload["stream"] is False
        assert payload["think"] is True
        assert payload["options"] == {
            "num_ctx": 8192,
            "num_predict": 4096,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
        }
        assert payload["messages"] == [{"role": "user", "content": "hola"}]
        assert payload["tools"] == []
        return httpx.Response(
            200, json=response({"role": "assistant", "content": "hola", "thinking": "x"})
        )

    provider = provider_for(handler)
    assert provider.chat([{"role": "user", "content": "hola"}], [])["thinking"] == "x"


@pytest.mark.parametrize("status", [400, 404, 500])
def test_http_errors_have_actionable_messages(status: int) -> None:
    provider = provider_for(lambda request: httpx.Response(status, json={"error": "internal"}))
    with pytest.raises(ProviderError, match=f"HTTP {status}"):
        provider.chat([], [])


@pytest.mark.parametrize("exception", [httpx.ConnectError, httpx.ReadTimeout])
def test_connection_and_timeout_errors(exception: type[httpx.RequestError]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exception("failure", request=request)

    with pytest.raises(ProviderError):
        provider_for(handler).chat([], [])


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"error": "failure"},
        {"done": False, "message": {"role": "assistant", "content": "partial"}},
        {
            "done": True,
            "done_reason": "length",
            "message": {"role": "assistant", "content": "partial"},
        },
        response(None),
        response({"role": "tool", "content": "oops"}),
        response({"role": "assistant", "content": 1}),
        response({"role": "assistant", "content": ""}),
        response({"role": "assistant", "content": "x", "tool_calls": {}}),
        response({"role": "assistant", "tool_calls": [None]}),
        response(
            {"role": "assistant", "tool_calls": [{"function": {"name": "x", "arguments": []}}]}
        ),
    ],
)
def test_rejects_malformed_or_incomplete_responses(payload: object) -> None:
    with pytest.raises(ProviderError):
        provider_for(lambda request: httpx.Response(200, json=payload)).chat([], [])


def test_rejects_non_json_body() -> None:
    with pytest.raises(ProviderError, match="JSON"):
        provider_for(lambda request: httpx.Response(200, text="not json")).chat([], [])


def test_accepts_tool_call_without_content() -> None:
    call = {"function": {"name": "obtener_fecha", "arguments": {}}}
    provider = provider_for(
        lambda request: httpx.Response(
            200, json=response({"role": "assistant", "tool_calls": [call]})
        )
    )
    assert provider.chat([], [])["tool_calls"] == [call]


@pytest.mark.parametrize("available", [True, False])
def test_check_confirms_exact_model_and_tools(available: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.14.11"})
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:4b"}] if available else []})
        assert request.url.path == "/api/show"
        assert json.loads(request.content) == {"model": "qwen3:4b"}
        return httpx.Response(200, json={"capabilities": ["completion", "tools"]})

    provider = provider_for(handler)
    if available:
        assert provider.check()["model"] == "qwen3:4b"
    else:
        with pytest.raises(ProviderError, match="ollama pull"):
            provider.check()


@pytest.mark.parametrize(
    ("requested", "supported", "valid"),
    [
        (True, [True], True),
        (False, [True], False),
        (False, [False, True], True),
        (True, [False], False),
    ],
)
def test_check_validates_thinking_controls(
    requested: bool, supported: list[bool], valid: bool
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.40.11"})
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:4b"}]})
        return httpx.Response(
            200, json={"capabilities": ["tools", "thinking"], "thinking": {"values": supported}}
        )

    with httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(Settings(think=requested), client=client)
        if valid:
            assert provider.check()["thinking"]["values"] == supported
        else:
            with pytest.raises(ProviderError, match="no admite think"):
                provider.check()
