"""El núcleo solo necesita este contrato, no los detalles HTTP de Ollama."""

from typing import Any, Protocol

Message = dict[str, Any]
ToolSchema = dict[str, Any]


class ProviderError(RuntimeError):
    """La inferencia no produjo una respuesta utilizable."""


class LLMProvider(Protocol):
    def chat(self, messages: list[Message], tools: list[ToolSchema]) -> Message:
        """Devuelve un mensaje assistant, con contenido y/o tool_calls."""
        ...
