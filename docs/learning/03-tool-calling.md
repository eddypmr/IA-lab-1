# 03 — Tool calling, JSON Schema y bucle del agente

[Índice](../README.md) · [Arquitectura](../architecture/phase-0-1.md)

## El modelo propone; Python ejecuta

Enviamos al modelo los nombres, descripciones y parámetros de las herramientas
permitidas. El modelo puede devolver una estructura como esta:

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": [{
    "function": {
      "name": "crear_archivo",
      "arguments": {"ruta": "python.txt", "contenido": "Python"}
    }
  }]
}
```

Esto todavía no crea ningún archivo. `ToolRegistry` busca el nombre en su registro,
valida argumentos y llama al handler Python. Nunca utiliza `eval`, `exec` ni importa
funciones a partir de texto del modelo.

## JSON Schema

Un esquema describe la forma de los argumentos, por ejemplo:

```json
{
  "type": "object",
  "properties": {
    "ruta": {"type": "string", "minLength": 1},
    "contenido": {"type": "string"}
  },
  "required": ["ruta", "contenido"],
  "additionalProperties": false
}
```

`required` evita parámetros ausentes. `type` comprueba tipos.
`additionalProperties: false` rechaza nombres inventados. La biblioteca `jsonschema`
valida antes de ejecutar; los esquemas no sirven únicamente para orientar al modelo.
El permiso para acceder a una ruta sigue comprobándose en `Workspace`.

## Observaciones y varias rondas

Después de la ejecución se añade al historial un mensaje `tool` con nombre y resultado:

```json
{
  "role": "tool",
  "tool_name": "crear_archivo",
  "content": "{\"ok\": true, \"result\": {\"ruta\": \"python.txt\", \"bytes\": 6}}"
}
```

`content` es una cadena que contiene JSON. En la siguiente inferencia el modelo ve qué
ocurrió y puede pedir un listado o una lectura. El historial conserva el mensaje del
asistente que solicitó las herramientas y cada observación correspondiente.

El bucle mínimo se puede expresar así:

```python
for ronda in range(max_iterations):
    respuesta = modelo(historial, esquemas)
    historial.append(respuesta)
    if not respuesta.tool_calls:
        return respuesta.content
    for llamada in respuesta.tool_calls:
        historial.append(ejecutar_y_validar(llamada))
```

El límite evita una secuencia interminable si el modelo insiste en herramientas.
Cuenta inferencias completas, no herramientas. Un máximo de 1 puede permitir crear
archivos, pero no deja otra inferencia para interpretar los resultados y responder.

## Aprender de errores

Un error de argumentos vuelve como observación estructurada. El modelo puede corregir
la siguiente llamada: esto es una consecuencia del bucle básico, sin planificador ni
sistema avanzado de reintentos. Los errores HTTP interrumpen el turno y muestran un
mensaje útil al usuario.

Que el modelo diga «creado» no demuestra que exista un archivo. Por eso las pruebas
comprueban los archivos en disco y las observaciones de `listar_archivos` y `leer_archivo`.
La prueba determinista verifica nuestro motor; la prueba real verifica también el
comportamiento de Qwen3, que puede variar entre versiones.

## Registrar una extensión de confianza

```python
from ai_agent_lab.tools.registry import Tool

registry.register(
    Tool(
        name="sumar",
        description="Suma dos enteros.",
        parameters={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        handler=lambda a, b: a + b,
    )
)
```

El esquema aparecerá en la siguiente inferencia. Registrar una función concede
capacidad de ejecutar ese código; los handlers son código de confianza y deben
devolver valores serializables como JSON.

Referencia del protocolo: [Tool calling de Ollama](https://docs.ollama.com/capabilities/tool-calling).
