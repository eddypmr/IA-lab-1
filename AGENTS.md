# Instrucciones de desarrollo

Lee `README.md`, `ROADMAP.md` y este archivo antes de cambios importantes.
`ROADMAP.md` es el documento maestro y el trabajo debe avanzar por fases.

- El alcance autorizado actualmente son las fases 0, 1 y 2. No iniciar la fase 3 hasta
  que el usuario lo indique explícitamente.
- Usar Python compatible con 3.10 y WSL2 Ubuntu 22.04.
- Mantener pocas dependencias, tipado y responsabilidades separadas. No introducir
  frameworks de agentes durante estas primeras fases.
- Las herramientas de archivos deben operar únicamente dentro del workspace,
  validar entradas y rechazar enlaces simbólicos y rutas de escape.
- El texto producido por un modelo nunca se evalúa ni ejecuta como código en el host.
  Los comandos y scripts solo pueden ejecutarse dentro del sandbox Docker.
- Mantener separadas las pruebas deterministas y la prueba opcional de Ollama real.
- Para verificar cambios: `.venv/bin/python -m pytest`, `.venv/bin/ruff check .` y
  `.venv/bin/ruff format --check .`.
- Para verificar Ollama real: `AI_AGENT_LAB_TEST_OLLAMA=1 .venv/bin/python -m pytest -m ollama -v`.
  Esta prueba usa la GPU/modelo local y un workspace temporal.
- Para verificar Docker real: `AI_AGENT_LAB_TEST_DOCKER=1 .venv/bin/python -m pytest -m docker -v`.
  Docker Desktop debe estar iniciado y su integración WSL habilitada.
- Documentar conceptos en `docs/learning/`, decisiones en `docs/decisions/` y actualizar
  el roadmap cuando se cumplan los criterios. Usar Markdown con enlaces relativos.
- No almacenar secretos, entornos virtuales ni archivos generados en Git.
- No montar el socket Docker en contenedores, habilitar la red ni conceder privilegios.
- No modificar configuraciones globales, instalar modelos ni avanzar fases por iniciativa propia.
