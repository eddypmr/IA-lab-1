# Verificación de la fase 2 — Docker Sandbox

**Fecha:** 2026-10-26.
**Estado:** validada con Docker real y aceptación integrada con Ollama.

## Disponibilidad observada

- WSL2 Ubuntu 22.04 y VS Code remoto están activos.
- No hay socket Docker accesible desde WSL en `/var/run/docker.sock`.
- `/usr/bin/docker` apunta a `/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker`, que no está presente.
- La CLI de Windows informa Docker 29.1.3, pero no se puede abrir el canal
  `dockerDesktopLinuxEngine`: su daemon no está en ejecución.
- `python:3.10-slim` no puede comprobarse mientras el daemon no responde.
- La cuenta WSL tiene UID/GID 1000 y pertenece al grupo `docker`.
- `python -m ai_agent_lab.main --check` confirma Ollama 0.40.11 y `qwen3:4b`, pero
  termina con código 1 porque falta la CLI Linux integrada en WSL.
- `.venv/bin/python -m pytest`: 151 pasaron; 4 pruebas opcionales se omitieron.
- `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .` y
  `.venv/bin/python -m pip check`: correctos.
- Las pruebas deterministas ejercitan argumentos de aislamiento, límites de salida,
  errores, timeout, rutas seguras y el paso de herramienta al historial del agente.

`Docker Desktop` requiere que arranque su daemon Linux y que Settings → Resources →
WSL Integration tenga habilitada la distro Ubuntu-22.04. Esta prueba no iniciará ni
modificará Docker Desktop automáticamente.

## Implementación

`DockerExecutor` arma argv sin shell host, valida la conexión local y la imagen,
monta un único workspace y limita red, usuario, raíz, capacidades, CPU, RAM, swap,
procesos, tmpfs, tiempo y texto capturado. `execute_python` comprueba ruta, extensión,
tipo de archivo y contenido UTF-8 antes de iniciar el contenedor.

La salida de cada flujo se drena de forma simultánea y se limita. El código de salida
se conserva; un timeout solicita parar el contenedor identificado por un nombre aleatorio,
después intenta matarlo y devuelve 124. No se hacen pulls implícitos.

## Pruebas por ejecutar con Docker activo

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
- La prueba manual interactiva también pasó: se inició el agente con
  `--num-ctx 12288 --num-predict 8192 --timeout 300`; Qwen creó `prueba.py`, listó
  el workspace y `execute_python` devolvió `exit_code=0` y stdout `42`.
- Con los valores por defecto (contexto 8192, generación 4096), esa misma petición
  manual terminó por longitud antes de producir una respuesta completa. Subir solo el
  timeout a 300 segundos no bastó; aumentar el contexto y el presupuesto de generación
  sí permitió completar el flujo en este caso.

Con esta evidencia, el criterio de aceptación de la fase queda cumplido.
