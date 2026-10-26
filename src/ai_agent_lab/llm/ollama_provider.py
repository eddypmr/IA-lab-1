"""Cliente síncrono de la API HTTP nativa de Ollama, sin SDK de agentes."""

import json
from copy import deepcopy
from typing import Any

import httpx

from ai_agent_lab.config.settings import Settings
from ai_agent_lab.llm.base import Message, ProviderError, ToolSchema


class OllamaProvider:
    def __init__(self, settings: Settings, *, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=settings.host,
            timeout=settings.timeout_seconds,
            trust_env=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OllamaProvider":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError(
                "Ollama superó el timeout. Revisa el servicio o aumenta timeout_seconds."
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                message = (
                    f"Modelo o endpoint no encontrado. Comprueba ollama pull {self.settings.model}."
                )
            else:
                message = "Revisa los registros del servidor Ollama."
            raise ProviderError(f"Ollama devolvió HTTP {status}. {message}") from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                f"No se pudo conectar con Ollama en {self.settings.host}. "
                "Comprueba ollama serve y la dirección configurada."
            ) from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("Ollama devolvió JSON inválido.") from exc
        if not isinstance(data, dict) or "error" in data:
            raise ProviderError("Ollama devolvió una respuesta inválida o un error.")
        return data

    def check(self) -> dict[str, Any]:
        """Comprueba servicio, modelo exacto y soporte de herramientas sin inferencia."""
        version = self._request("GET", "/api/version").get("version", "desconocida")
        models = self._request("GET", "/api/tags").get("models")
        if not isinstance(models, list):
            raise ProviderError("Ollama devolvió una lista de modelos inválida.")
        names = {
            item["name"]
            for item in models
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        if self.settings.model not in names:
            raise ProviderError(
                f"No está disponible {self.settings.model}. "
                f"Ejecuta ollama pull {self.settings.model}."
            )
        model = self._request("POST", "/api/show", json={"model": self.settings.model})
        capabilities = model.get("capabilities", [])
        if not isinstance(capabilities, list) or "tools" not in capabilities:
            raise ProviderError("El modelo seleccionado no declara soporte de herramientas.")
        thinking = model.get("thinking")
        if (
            isinstance(thinking, dict)
            and isinstance(thinking.get("values"), list)
            and self.settings.think not in thinking["values"]
        ):
            supported = json.dumps(thinking["values"])
            raise ProviderError(
                f"El modelo no admite think={str(self.settings.think).lower()}. "
                f"Valores permitidos por /api/show: {supported}. Revisa la configuración."
            )
        return {
            "version": version,
            "model": self.settings.model,
            "capabilities": capabilities,
            "thinking": thinking,
        }

    def chat(self, messages: list[Message], tools: list[ToolSchema]) -> Message:
        data = self._request(
            "POST",
            "/api/chat",
            json={
                "model": self.settings.model,
                "messages": messages,
                "tools": tools,
                "stream": False,
                "think": self.settings.think,
                "options": {
                    "num_ctx": self.settings.num_ctx,
                    "num_predict": self.settings.num_predict,
                    "temperature": self.settings.temperature,
                    "top_p": self.settings.top_p,
                    "top_k": self.settings.top_k,
                    "min_p": 0.0,
                },
            },
        )
        if data.get("done") is not True or data.get("done_reason") == "length":
            raise ProviderError(
                "Respuesta incompleta de Ollama; no se ejecutarán sus herramientas. "
                "Revisa num_predict y num_ctx si se agotó el presupuesto de tokens."
            )
        message = data.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise ProviderError("Ollama no devolvió un mensaje assistant válido.")
        content = message.get("content", "")
        calls = message.get("tool_calls", [])
        if not isinstance(content, str) or not isinstance(calls, list):
            raise ProviderError("Contenido o llamadas a herramientas inválidos.")
        for call in calls:
            function = call.get("function") if isinstance(call, dict) else None
            if (
                not isinstance(function, dict)
                or not isinstance(function.get("name"), str)
                or not function["name"].strip()
                or not isinstance(function.get("arguments"), (dict, str))
            ):
                raise ProviderError("Llamada a herramienta mal formada; se rechaza la respuesta.")
        if not content.strip() and not calls:
            raise ProviderError("Ollama devolvió una respuesta vacía.")
        result = deepcopy(message)
        result["content"] = content
        return result
