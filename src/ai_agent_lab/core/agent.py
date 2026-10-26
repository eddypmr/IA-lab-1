"""Bucle mínimo: inferencia → herramientas → observaciones → inferencia."""

import json
import logging
from copy import deepcopy

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.llm.base import LLMProvider, Message, ProviderError
from ai_agent_lab.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class IterationLimitError(RuntimeError):
    """La tarea no terminó dentro de los límites configurados."""


class Agent:
    def __init__(self, provider: LLMProvider, tools: ToolRegistry, settings: Settings) -> None:
        self.provider = provider
        self.tools = tools
        self.settings = settings
        self.messages: list[Message] = []
        self.reset()

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.settings.system_prompt}]

    def run(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("La instrucción no puede estar vacía.")
        self.messages.append({"role": "user", "content": prompt})
        try:
            for iteration in range(1, self.settings.max_iterations + 1):
                logger.debug("Ronda de inferencia %d/%d", iteration, self.settings.max_iterations)
                message = self.provider.chat(deepcopy(self.messages), self.tools.schemas())
                calls = message.get("tool_calls", [])
                if len(calls) > self.settings.max_tool_calls_per_response:
                    raise IterationLimitError(
                        "Demasiadas herramientas en una respuesta; no ejecutadas."
                    )
                self.messages.append(deepcopy(message))
                if not calls:
                    return message["content"]
                # Secuencial: una lectura puede depender de una creación anterior del mismo lote.
                for call in calls:
                    function = call["function"]
                    result = self.tools.execute(function["name"], function["arguments"])
                    observation: Message = {
                        "role": "tool",
                        "tool_name": function["name"],
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                    if call.get("id"):
                        observation["tool_call_id"] = call["id"]
                    self.messages.append(observation)
            raise IterationLimitError(
                f"Se alcanzó el límite de {self.settings.max_iterations} rondas "
                "sin respuesta final. "
                "Las herramientas ya ejecutadas conservan sus efectos."
            )
        except (ProviderError, IterationLimitError) as exc:
            # Conserva observaciones de acciones reales; el siguiente turno puede inspeccionarlas.
            self.messages.append({"role": "assistant", "content": f"Turno interrumpido: {exc}"})
            raise
