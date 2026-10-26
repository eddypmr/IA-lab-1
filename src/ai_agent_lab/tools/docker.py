"""Registra únicamente operaciones de código dentro del DockerExecutor autorizado."""

from ai_agent_lab.sandbox.docker_executor import DockerExecutor
from ai_agent_lab.tools.registry import Tool, ToolRegistry


def register_docker_tools(registry: ToolRegistry, executor: DockerExecutor) -> None:
    argument = {"type": "string", "maxLength": 4096}
    registry.register(
        Tool(
            name="execute_command",
            description=(
                "Ejecuta una lista de argumentos directamente, sin shell del host, en un "
                "contenedor Docker sin red, como usuario no root y con recursos limitados. "
                "Devuelve exit_code, stdout, stderr, timed_out y output_truncated."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "items": argument,
                        "minItems": 1,
                        "maxItems": 128,
                        "description": 'Ejemplo: ["python", "-c", "print(1 + 1)"].',
                    }
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            handler=lambda command: executor.execute(command),
        )
    )
    registry.register(
        Tool(
            name="execute_python",
            description=(
                "Ejecuta un archivo .py ya existente en el workspace dentro del mismo "
                "contenedor Docker; devuelve código de salida y salida acotada."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 4096,
                        "description": "Ruta relativa a un script .py del workspace.",
                    },
                    "argumentos": {
                        "type": "array",
                        "items": argument,
                        "maxItems": 32,
                    },
                },
                "required": ["ruta"],
                "additionalProperties": False,
            },
            handler=lambda ruta, argumentos=None: executor.execute_python(ruta, argumentos),
        )
    )
