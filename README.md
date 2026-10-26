# AI Agent Lab

Agente local de aprendizaje construido desde cero con Python y Ollama.
El alcance autorizado actual son las **fases 0, 1 y 2** de [ROADMAP.md](ROADMAP.md), documento maestro.

## Instalación en WSL2

Requiere Python 3.10 o posterior dentro de WSL2, Ollama activo y el modelo `qwen3:4b`.
El desarrollo se ha realizado con Python 3.10.12. No se necesitan claves de API ni
frameworks de agentes.

```bash
cd /home/eddy/IAS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock -e '.[dev]'
```

El lock instala las versiones verificadas. Para resolver versiones nuevas dentro
de los rangos de `pyproject.toml`, usa `python -m pip install -e '.[dev]'`.
Si falta el módulo `venv` en Ubuntu, instala `python3-venv` mediante el gestor del sistema.

Comprueba el servicio y el modelo:

```bash
ollama --version
ollama list
python -m ai_agent_lab.main --check
```

Si el servicio no está activo, ejecuta `ollama serve` en otra terminal. Si el modelo
no está descargado, usa `ollama pull qwen3:4b`. Estas acciones solo son necesarias
cuando las comprobaciones indican que faltan.

El proyecto está abierto en tu ventana de VS Code conectada a `WSL: Ubuntu-22.04`.
La conexión y las extensiones de Python y Ruff ya están verificadas. La configuración
`.vscode/` selecciona `.venv/bin/python`. En [esta guía](docs/learning/01-entorno-python.md#comprobar-vs-code-y-sus-extensiones)
explico cómo comprobar la selección del intérprete en la interfaz. Para Obsidian,
abre esta carpeta como vault y navega por [docs/README.md](docs/README.md).

## Ejecutar

```bash
python -m ai_agent_lab.main
```

La sesión conserva el historial en RAM. Usa `/salir`, Ctrl+D o Ctrl+C para terminar;
`/reset` limpia la conversación. Los archivos permanecen en `workspace/`.

Ejemplo de tarea:

> Crea python.txt, docker.txt y cuda.txt con una explicación breve de cada tecnología.
> Después lista el directorio y lee los tres archivos para comprobar sus contenidos.

También puedes ejecutar una sola tarea y salir:

```bash
python -m ai_agent_lab.main --verbose --prompt \
  "Crea python.txt, docker.txt y cuda.txt con una explicación breve de cada tecnología. Después lista el directorio y lee los tres archivos para comprobarlos."
```

No se sobrescriben archivos existentes. Para repetir una demostración sin tocar los
anteriores, elige un workspace nuevo:

```bash
python -m ai_agent_lab.main --workspace workspace/demo-02
```

`ai-agent-lab` es equivalente a `python -m ai_agent_lab.main` tras instalar el paquete.

## Configuración

Los valores por defecto permiten arrancar sin archivos adicionales. Para usar y editar
el ejemplo de configuración:

```bash
python -m ai_agent_lab.main --config configs/default.json
python -m ai_agent_lab.main --num-ctx 8192 --num-predict 4096 --max-iterations 8 --timeout 180
python -m ai_agent_lab.main --system-prompt-file mi-prompt.txt
python -m ai_agent_lab.main --help
```

| Opción | Valor inicial | Significado |
|---|---|---|
| `host` | `http://127.0.0.1:11434` | API HTTP de Ollama. |
| `model` | `qwen3:4b` | Nombre exacto del modelo instalado. |
| `workspace` | `workspace/` | Única raíz de archivos autorizada. |
| `num_ctx` | 8192 | Contexto solicitado, en tokens. |
| `num_predict` | 4096 | Máximo de tokens generados por inferencia, incluido el razonamiento. |
| `max_iterations` | 12 | Máximo de inferencias por turno, incluida la respuesta final. |
| `max_tool_calls_per_response` | 8 | Máximo de llamadas en una respuesta. |
| `temperature` | 0.6 | Muestreo inicial para Qwen3 con razonamiento. |
| `top_p` / `top_k` | 0.95 / 20 | Parámetros de muestreo. |
| `think` | `true` | Compatible con la variante instalada, que solo permite este valor. |
| `timeout_seconds` | 120 | Timeout de cada petición HTTP. |

Precedencia: valores iniciales → JSON → argumentos CLI. La ruta `workspace` del JSON
es relativa a ese archivo; `--workspace` es relativo a la terminal actual.
`system_prompt` también puede definirse como texto en el JSON. No se carga `.env`.

La CLI comprueba el modelo y sus capacidades antes de empezar. Si `/api/show` publica
los valores permitidos de `think`, rechaza una configuración incompatible. El nombre
`qwen3:4b` puede apuntar a variantes diferentes: la instalada durante el desarrollo
declara únicamente `think: true`. No se debe asumir que todas permiten desactivarlo.
La CLI muestra la respuesta final; conserva el campo de razonamiento para el protocolo.

El contexto inicial busca un consumo moderado en una GPU de 6 GB. Comprueba la
residencia real después de una tarea con `ollama ps`: el tamaño del contexto y otros
programas pueden cambiar el consumo. No se instala ni se modifica CUDA desde el proyecto.

## Arquitectura y herramientas

```text
CLI → Agent → OllamaProvider → Ollama / qwen3:4b
         ↕
    ToolRegistry → fecha / archivos / Docker Sandbox
```

El modelo solicita una función; Python valida sus argumentos con JSON Schema,
ejecuta la función y devuelve el resultado al historial. El modelo recibe esas
observaciones en la siguiente inferencia hasta producir una respuesta final.

| Herramienta | Función |
|---|---|
| `obtener_fecha()` | Fecha y hora con zona del sistema. |
| `listar_archivos(ruta=".")` | Lista hasta 200 entradas, sin seguir symlinks. |
| `leer_archivo(ruta)` | Lee un archivo regular UTF-8 de hasta 64 KiB. |
| `crear_archivo(ruta, contenido)` | Crea un archivo UTF-8 de hasta 64 KiB, sin sobrescribir. |
| `execute_command(command)` | Ejecuta un argv dentro de Docker, sin shell en el host. |
| `execute_python(ruta, argumentos=[])` | Ejecuta un script `.py` del workspace en Docker. |

Las rutas deben ser relativas al workspace. Los directorios padres deben existir.
Los comandos corren en Docker con red desactivada, filesystem raíz de solo lectura,
usuario no root y límites de recursos. Solo se monta el workspace. El texto del modelo
nunca se ejecuta en el host.

La imagen `python:3.10-slim` debe existir localmente. Docker Desktop debe estar activo
y con Ubuntu-22.04 habilitado en Settings → Resources → WSL Integration. Comprueba
la conexión con `docker info`; el agente no descarga imágenes automáticamente.
`python -m ai_agent_lab.main --check` valida Ollama, Docker y la imagen local.

Los registros muestran nombres de herramientas y estados; `--verbose` añade rondas.
Los fallos se devuelven al modelo como observaciones o se presentan como errores de
inferencia. El límite de rondas no deshace acciones ya ejecutadas. El historial no
se guarda entre sesiones y todavía no se resume si excede el contexto.

Consulta la [arquitectura detallada](docs/architecture/phase-0-1.md) y los
[conceptos aprendidos](docs/README.md).

## Pruebas

```bash
python -m pytest
ruff check .
ruff format --check .
python -m pip check
```

Las pruebas habituales no requieren Ollama ni GPU. Cubren el contrato HTTP, la
validación, las rutas y enlaces simbólicos, el historial, la CLI y una aceptación
determinista que crea y verifica tres archivos usando todos los componentes reales
salvo el transporte del modelo.

Las pruebas simuladas del sandbox Docker también forman parte de la suite. Para usar
Docker real, primero comprueba `docker info`, descarga manualmente la imagen si hace
falta (`docker pull python:3.10-slim`) y ejecuta:

```bash
AI_AGENT_LAB_TEST_DOCKER=1 python -m pytest -m docker -v
```

Para probar también el modelo local:

```bash
AI_AGENT_LAB_TEST_OLLAMA=1 python -m pytest -m ollama -v -s --log-cli-level=INFO
```

Esta prueba usa un workspace temporal y comprueba los archivos, sus lecturas y un
listado real mediante las herramientas. Requiere el servicio y puede tardar más o
variar con el modelo. Opcionalmente admite `OLLAMA_HOST` y `OLLAMA_MODEL` para esta prueba.
La CLI usa `--host` y `--model`.

Los códigos de salida de la CLI son 0 para una ejecución normal, 1 para errores o
límites y 130 para Ctrl+C. Un error de herramienta también puede comunicarse en
la respuesta normal del modelo; estado 0 por sí solo no certifica que el objetivo
se haya completado.

## Estado

Las fases 0, 1 y 2 tienen implementación y pruebas; la fase 2 también pasó sus pruebas
con Docker real y la aceptación integrada con Ollama. Véanse la
[verificación fase 0–1](docs/experiments/phase-0-1-validation.md),
[verificación fase 2](docs/experiments/phase-2-validation.md) y
[guía del sandbox](docs/learning/05-sandbox-docker.md).
