"""CLI de aprendizaje: python -m ai_agent_lab.main."""

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

from ai_agent_lab.config.settings import Settings, load_settings
from ai_agent_lab.core.agent import Agent, IterationLimitError
from ai_agent_lab.llm.base import ProviderError
from ai_agent_lab.llm.ollama_provider import OllamaProvider
from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.docker import register_docker_tools
from ai_agent_lab.tools.filesystem import Workspace, register_default_tools
from ai_agent_lab.tools.registry import ToolError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Agent Lab — agente local con Ollama")
    parser.add_argument("--config", type=Path, help="Archivo JSON de configuración")
    parser.add_argument("--model", help="Modelo Ollama (por defecto: qwen3:4b)")
    parser.add_argument("--host", help="URL del servidor Ollama")
    parser.add_argument("--workspace", type=Path, help="Directorio autorizado para archivos")
    parser.add_argument("--max-iterations", type=int, help="Máximo de inferencias por turno")
    parser.add_argument("--num-ctx", type=int, help="Tamaño de contexto en tokens")
    parser.add_argument("--num-predict", type=int, help="Máximo de tokens generados por inferencia")
    parser.add_argument(
        "--timeout", dest="timeout_seconds", type=float, help="Timeout HTTP en segundos"
    )
    parser.add_argument("--docker-image", help="Imagen Linux local para ejecutar código")
    parser.add_argument("--sandbox-timeout", type=float, help="Timeout de cada ejecución en Docker")
    parser.add_argument("--system-prompt-file", type=Path, help="System prompt UTF-8 personalizado")
    parser.add_argument("--prompt", "-p", help="Ejecutar una tarea y salir")
    parser.add_argument(
        "--check", action="store_true", help="Comprobar Ollama y el modelo sin inferencia"
    )
    parser.add_argument("--verbose", action="store_true", help="Mostrar rondas de inferencia")
    return parser


def settings_from_args(args: argparse.Namespace) -> Settings:
    settings = load_settings(args.config)
    overrides = {
        name: getattr(args, name)
        for name in (
            "model",
            "host",
            "workspace",
            "max_iterations",
            "num_ctx",
            "num_predict",
            "timeout_seconds",
        )
        if getattr(args, name) is not None
    }
    if args.system_prompt_file is not None:
        overrides["system_prompt"] = args.system_prompt_file.read_text(encoding="utf-8")
    sandbox_overrides = {
        name: value
        for name, value in (
            ("image", args.docker_image),
            ("timeout_seconds", args.sandbox_timeout),
        )
        if value is not None
    }
    if sandbox_overrides:
        overrides["sandbox"] = replace(settings.sandbox, **sandbox_overrides)
    return replace(settings, **overrides)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    # Evita registrar tráfico HTTP y no registra argumentos ni contenido de archivos.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    try:
        settings = settings_from_args(args)
        with OllamaProvider(settings) as provider:
            report = provider.check()
            if args.check:
                print(f"Ollama {report['version']} | modelo: {report['model']} | tools: sí")
                print(f"Contexto solicitado: {settings.num_ctx} tokens")
                print(f"Generación máxima: {settings.num_predict} tokens | think: {settings.think}")
                try:
                    docker = DockerExecutor(None, settings.sandbox).check()
                except ToolError as exc:
                    print(f"Docker: no disponible — {exc}", file=sys.stderr)
                    return 1
                print(
                    f"Docker {docker['server']} | endpoint local: {docker['endpoint']} "
                    f"| imagen: {docker['image']}"
                )
                return 0
            workspace = Workspace(settings.workspace)
            tools = register_default_tools(workspace)
            register_docker_tools(tools, DockerExecutor(workspace, settings.sandbox))
            agent = Agent(provider, tools, settings)
            if args.prompt is not None:
                print(agent.run(args.prompt))
                return 0
            print(f"AI Agent Lab | {settings.model} | workspace: {workspace.root}")
            print("/salir para terminar; /reset para limpiar el historial en memoria.")
            while True:
                try:
                    prompt = input("\nTú> ").strip()
                except EOFError:
                    print()
                    return 0
                if prompt == "/salir":
                    return 0
                if prompt == "/reset":
                    agent.reset()
                    print("Historial reiniciado.")
                    continue
                if not prompt:
                    continue
                try:
                    print(f"\nAgente> {agent.run(prompt)}")
                except (ProviderError, IterationLimitError) as exc:
                    print(f"Error: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nEjecución interrumpida.", file=sys.stderr)
        return 130
    except (OSError, ValueError, ProviderError, IterationLimitError, ToolError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
