from collections.abc import Callable
from unittest.mock import Mock

import pytest
from jsonschema import SchemaError

from ai_agent_lab.tools.registry import Tool, ToolError, ToolRegistry


@pytest.mark.parametrize("arguments", [{"numero": 3}, '{"numero": 3}'])
def test_executes_only_registered_valid_tool(registry: ToolRegistry, arguments: object) -> None:
    assert registry.execute("doblar", arguments) == {"ok": True, "result": 6}


@pytest.mark.parametrize(
    "arguments",
    [{}, {"numero": "3"}, {"numero": True}, {"numero": 3, "extra": 1}, [], None, "{broken"],
)
def test_rejects_arguments_before_execution(
    make_tool: Callable[..., Tool], arguments: object
) -> None:
    handler = Mock()
    registry = ToolRegistry()
    registry.register(make_tool(handler=handler))
    result = registry.execute("doblar", arguments)
    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_arguments"
    handler.assert_not_called()


def test_unknown_tool_does_not_resolve_python_names(registry: ToolRegistry) -> None:
    result = registry.execute("__import__", {"name": "os"})
    assert result["error"]["code"] == "unknown_tool"


def test_registers_dynamically_and_rejects_duplicates(
    registry: ToolRegistry, make_tool: Callable[..., Tool]
) -> None:
    registry.register(make_tool("otra"))
    assert registry.execute("otra", {"numero": 2})["result"] == 4
    with pytest.raises(ValueError, match="duplicado"):
        registry.register(make_tool("otra"))


def test_schema_exports_cannot_modify_registry(registry: ToolRegistry) -> None:
    exported = registry.schemas()
    exported[0]["function"]["parameters"]["required"] = []
    assert registry.execute("doblar", {})["ok"] is False


def test_rejects_invalid_schema() -> None:
    with pytest.raises(SchemaError):
        ToolRegistry().register(Tool("bad", "bad", {"type": "inventado"}, lambda: None))


@pytest.mark.parametrize(
    ("exception", "code"),
    [
        (ToolError("Fallo esperado"), "tool_error"),
        (PermissionError("/secret/path"), "filesystem_error"),
        (RuntimeError("secret content"), "execution_error"),
    ],
)
def test_tool_errors_are_structured_and_do_not_leak_details(
    make_tool: Callable[..., Tool], exception: Exception, code: str
) -> None:
    def fail(numero: int) -> None:
        raise exception

    registry = ToolRegistry()
    registry.register(make_tool(handler=fail))
    result = registry.execute("doblar", {"numero": 1})
    assert result["error"]["code"] == code
    assert "secret" not in result["error"]["message"]


def test_non_serializable_result_is_an_error(make_tool: Callable[..., Tool]) -> None:
    registry = ToolRegistry()
    registry.register(make_tool(handler=lambda numero: {numero}))
    assert registry.execute("doblar", {"numero": 1})["error"]["code"] == "execution_error"
