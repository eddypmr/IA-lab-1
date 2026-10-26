# Decisión 0002 — Ejecutar comandos únicamente dentro de Docker

**Estado:** implementada y validada con Docker integrado en WSL.
**Fecha:** 2026-10-26.
**Roadmap:** [ROADMAP.md](../../ROADMAP.md).

## Contexto

La fase 2 añade ejecución de código pero el agente no debe ejecutar comandos arbitrarios
en Windows o WSL. Docker debe limitar directorios, red, usuario, recursos y duración.
El sandbox debe permitir ejecutar scripts de Python escritos en `workspace/` y observar
su salida y código de salida.

## Decisiones

1. Usar la CLI Docker local mediante `subprocess` con argv y `shell=False`; no añadir
   Docker SDK ni frameworks.
2. Modelar `execute_command` como lista de argumentos. El ejecutable nunca concatena
   una cadena en un shell del host.
3. Mantener `execute_python` separado para ejecutar un `.py` comprobado con las
   restricciones de `Workspace`.
4. Permitir un único bind mount de la raíz del workspace a `/workspace`.
5. Rechazar contextos Docker por TCP o SSH: el directorio bind-mounted debe pertenecer
   al mismo host Linux local.
6. No montar home, socket Docker, credenciales ni directorios exteriores.
7. Usar imagen local y `--pull=never`. Pedir al usuario que descargue explícitamente
   `python:3.10-slim` si está ausente.
8. Retornar salidas por flujo con límite, timeout con parada del contenedor y el
   código de salida real.
9. Hacer deterministas las pruebas unitarias con clientes `Popen`/`run` sustituidos.
   La aceptación integrada con Ollama y Docker solo se activa explícitamente.

## Consecuencias

Los programas ejecutados tienen acceso de escritura al workspace solicitado y pueden
cambiarlo. Docker aporta límites de kernel y cgroups, pero no una VM de kernel separado.
`Docker Desktop` debe ejecutarse y tener integración WSL en la misma distribución de
Ubuntu. La integración se habilitó y la prueba real pasó; véase
[el registro de fase 2](../experiments/phase-2-validation.md).
