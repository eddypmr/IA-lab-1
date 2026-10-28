# Verificación de la fase 2 — Docker Sandbox

**Fecha:** 2026-10-28.
**Estado:** validada con Docker real y aceptación integrada con Ollama.

## Entorno y disponibilidad

En una comprobación inicial Docker Desktop estaba instalado, pero el daemon Linux no
era accesible desde WSL: faltaban la CLI integrada y el socket. Después se habilitó
la integración WSL de Docker Desktop. Las pruebas reales posteriores ejecutaron
contenedores desde Ubuntu y pasaron, lo que confirma que CLI, daemon e imagen estaban
disponibles en ese momento.

El usuario informó que su entorno es WSL2 Ubuntu 22.04 con Ollama y `qwen3:4b`. En la
comprobación inicial local se observó Python 3.10.12 y Ollama 0.40.11.

## Implementación

`DockerExecutor` arma argv sin shell host, valida la conexión local y la imagen,
monta un único workspace y limita red, usuario, raíz, capacidades, CPU, RAM, swap,
procesos, tmpfs, tiempo y texto capturado. `execute_python` comprueba ruta, extensión,
tipo de archivo y contenido UTF-8 antes de iniciar el contenedor.

La salida de cada flujo se drena de forma simultánea y se limita. El código de salida
se conserva; un timeout solicita parar el contenedor identificado por un nombre aleatorio,
después intenta matarlo y devuelve 124. No se hacen pulls implícitos.

## Cómo reproducir las pruebas reales

```bash
docker info
docker pull python:3.10-slim
AI_AGENT_LAB_TEST_DOCKER=1 python -m pytest -m docker -v
AI_AGENT_LAB_TEST_OLLAMA=1 AI_AGENT_LAB_TEST_DOCKER=1 \
  python -m pytest -m acceptance -v
```

Resultados aportados desde WSL el 2026-10-26:

- `AI_AGENT_LAB_TEST_DOCKER=1 .venv/bin/python -m pytest -m docker -v`: 2 pasaron;
  la aceptación integrada se omitió en este comando porque no estaba habilitada la
  variable de Ollama.
- `AI_AGENT_LAB_TEST_OLLAMA=1 AI_AGENT_LAB_TEST_DOCKER=1 .venv/bin/python -m pytest
  -m acceptance -v`: la prueba integrada pasó en 87,16 s.
- La aceptación comprobó que Qwen creó `sum.py`, que el contenedor lo ejecutó y que
  el agente recibió el código de salida 0 y el resultado 42.
- La prueba manual interactiva pasó el 2026-10-28: se inició el agente con
  `--num-ctx 12288 --num-predict 8192 --timeout 300`; Qwen creó `prueba.py`, listó
  el workspace y `execute_python` devolvió `exit_code=0` y stdout `42`.
- Con los valores por defecto (contexto 8192, generación 4096), esa misma petición
  manual terminó por longitud antes de producir una respuesta completa. Subir solo el
  timeout a 300 segundos no bastó; aumentar el contexto y el presupuesto de generación
  sí permitió completar el flujo en este caso.

Con esta evidencia, el criterio de aceptación de la fase queda cumplido.
