from collections.abc import Callable
from pathlib import Path

import pytest

from ai_agent_lab.tools.filesystem import Workspace
from ai_agent_lab.tools.registry import Tool, ToolRegistry


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / "workspace")


@pytest.fixture
def make_tool() -> Callable[..., Tool]:
    def factory(name: str = "doblar", handler: Callable[..., object] | None = None) -> Tool:
        return Tool(
            name=name,
            description="Duplica un entero.",
            parameters={
                "type": "object",
                "properties": {"numero": {"type": "integer"}},
                "required": ["numero"],
                "additionalProperties": False,
            },
            handler=handler or (lambda numero: numero * 2),
        )

    return factory


@pytest.fixture
def registry(make_tool: Callable[..., Tool]) -> ToolRegistry:
    tools = ToolRegistry()
    tools.register(make_tool())
    return tools
