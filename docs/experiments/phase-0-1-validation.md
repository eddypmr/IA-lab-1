# Verificación de las fases 0 y 1

**Fecha:** 2026-10-26.
**Alcance:** [fases 0 y 1](../../ROADMAP.md); fase 2 sin iniciar.

## Entorno observado

| Componente | Resultado |
|---|---|
| Sistema | Linux WSL2 en Windows, entorno de trabajo `/home/eddy/IAS`. |
| Python | 3.10.12, con `.venv/` dentro del proyecto. |
| Git | 2.34.1, repositorio inicializado en `main`. |
| CPU | Intel Core i7-9750H, 12 procesadores lógicos. |
| Memoria | Windows detecta 31,85 GB; WSL tiene asignados 15,54 GB en `code --status`. |
| VS Code | Code 1.143.1; `code --status` identifica la ventana `IAS [WSL: Ubuntu-22.04]`. |
| Extensiones WSL | Python 2026.10.0 y Ruff 2026.90.0, confirmadas en `code --list-extensions --show-versions`. |
| Ollama | 0.40.11; difiere de la 0.14.11 indicada inicialmente. |
| Modelo | `qwen3:4b`, 4.0B, Q4_K_M, digest inicial `359d7dd4bcda`. |
| Capacidades | `completion`, `tools`, `thinking`. |
| Modos de razonamiento | `/api/show` devuelve `thinking.values: [true]`. |
| GPU | NVIDIA GeForce RTX 2060, 6144 MiB, accesible desde WSL fuera del sandbox. |
| Configuración final | 8192 tokens de contexto, 4096 de generación, `think: true`. |
| Muestreo | Temperatura 0,6; top_p 0,95; top_k 20; min_p 0. |
| Carga observada | `ollama ps`: 3,9 GB, 100 % GPU y contexto 8192. |

Las comprobaciones de Ollama, NVIDIA y Git requirieron salir del sandbox de esta
sesión, que bloqueaba el servicio local, NVML y la escritura en `.git`. El proyecto
no necesita permisos elevados al usarse normalmente desde una terminal WSL.
No se modificaron la instalación del modelo, los drivers ni la configuración global.

## Resultados finales

Con el entorno virtual activado:

| Comando | Resultado |
|---|---|
| `python -m pytest` | 116 correctas; 1 integración real omitida por defecto. |
| `ruff check .` | Correcto. |
| `ruff format --check .` | Correcto. |
| `python -m pip check` | Sin incompatibilidades de dependencias. |
| `python -m ai_agent_lab.main --config configs/default.json --check` | Servicio, modelo, herramientas y modo de razonamiento compatibles. |
| `code --status` | La ventana activa `IAS` y el entorno remoto son WSL Ubuntu 22.04. |
| `code --list-extensions --show-versions` | Python y Ruff figuran instaladas en WSL Ubuntu 22.04. |
| `AI_AGENT_LAB_TEST_OLLAMA=1 python -m pytest -m ollama -v -s --log-cli-level=INFO` | 1 correcta; 116 no seleccionadas; 81,30 segundos. |

## Aceptación real

La prueba pide al modelo crear `python.txt`, `docker.txt` y `cuda.txt` con textos
breves sobre cada tecnología. Después solicita un listado y la lectura de los tres.

Se observaron estas operaciones reales, todas con resultado correcto:

```text
crear_archivo × 3
listar_archivos × 1
leer_archivo × 3
respuesta final del modelo
```

La prueba comprueba los archivos en disco, los nombres presentes en el listado y las
observaciones de creación y lectura. Se realiza sobre un directorio temporal creado
por Pytest; no deja archivos de demostración en el workspace personal del usuario.
El modelo puede emitir varias llamadas en una respuesta. El motor las ejecuta en
orden y devuelve todas las observaciones antes de la siguiente inferencia.

La aceptación determinista reproduce este contrato mediante `httpx.MockTransport`:
proveedor, registro, bucle y archivos son reales; las respuestas HTTP están controladas.
No requiere Ollama ni GPU. Así se puede distinguir un fallo del motor de variaciones
de comportamiento del modelo.

## Experimentos que motivaron los valores finales

1. La configuración inicial con temperatura 0 y `think: false` agotó el timeout de
   120 segundos. No ejecutó herramientas. Los registros mostraron generación activa
   en GPU; no era un problema de conectividad.
2. Se inspeccionaron plantilla y metadatos. La descarga de `qwen3:4b` solo permite
   razonamiento activado. Se ajustó `think`, se adoptó muestreo no voraz y se añadieron
   pruebas de compatibilidad del modo solicitado.
3. Con 2048 tokens de generación la tarea completa devolvió una respuesta truncada.
   El proveedor la rechazó antes de ejecutar sus herramientas.
4. Una solicitud aislada produjo una llamada válida. Con 8192 tokens de contexto y
   4096 de generación, la tarea completa pasó y el modelo siguió al 100 % en GPU.

Esta evidencia justifica los valores iniciales para la descarga actual. No garantiza
la misma latencia ni el mismo comportamiento con otras versiones o tareas más largas.
Las respuestas no se muestran progresivamente: durante el razonamiento puede haber
una espera apreciable; `--verbose` permite ver la ronda activa.

## Límites de la verificación

Se ha probado Ollama 0.40.11, sin instalar 0.14.11 para repetir el experimento.
La prueba real es una ejecución satisfactoria, no una evaluación estadística de fiabilidad.
El límite del workspace cubre las herramientas incluidas y no sustituye un sandbox
del sistema operativo. La conexión WSL y las extensiones ya están comprobadas; la
barra de estado de Python permite verificar qué intérprete ha elegido la ventana activa.

[Problemas y límites](../learning/04-problemas-y-limites.md) ·
[Arquitectura](../architecture/phase-0-1.md) ·
[Índice de documentación](../README.md)
