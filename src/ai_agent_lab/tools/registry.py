"""Lista explícita de funciones permitidas y validación antes de ejecutarlas."""

import json
import logging
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Error esperado y apto para devolver al modelo."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._validators: dict[str, Draft202012Validator] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"Nombre de herramienta vacío o duplicado: {tool.name}.")
        Draft202012Validator.check_schema(tool.parameters)
        if tool.parameters.get("type") != "object":
            raise ValueError("Los parámetros de una herramienta deben ser un objeto JSON.")
        stored = Tool(tool.name, tool.description, deepcopy(tool.parameters), tool.handler)
        self._tools[tool.name] = stored
        self._validators[tool.name] = Draft202012Validator(stored.parameters)

    def schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": deepcopy(tool.parameters),
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: Any) -> dict[str, Any]:
        """Los fallos son observaciones estructuradas, no respuestas inventadas."""
        if name not in self._tools:
            return self._failure(name, "unknown_tool", "Herramienta no registrada.")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                return self._failure(
                    name, "invalid_arguments", "Los argumentos no son JSON válido."
                )
        try:
            self._validators[name].validate(arguments)
        except ValidationError as exc:
            # No incluir el valor rechazado: puede contener contenido sensible de archivos.
            location = ".".join(str(part) for part in exc.absolute_path) or "argumentos"
            return self._failure(
                name, "invalid_arguments", f"JSON Schema incumplido en {location}: {exc.validator}."
            )
        try:
            result = self._tools[name].handler(**arguments)
            json.dumps(result, ensure_ascii=False, allow_nan=False)
        except ToolError as exc:
            return self._failure(name, "tool_error", str(exc))
        except (OSError, UnicodeError):
            return self._failure(name, "filesystem_error", "No se pudo acceder al archivo UTF-8.")
        except Exception:
            return self._failure(
                name, "execution_error", "La herramienta produjo un error interno."
            )
        logger.info("Herramienta %s: ok", name)
        return {"ok": True, "result": result}

    @staticmethod
    def _failure(name: str, code: str, message: str) -> dict[str, Any]:
        logger.warning("Herramienta %s: %s", name, code)
        return {"ok": False, "error": {"code": code, "message": message}}
