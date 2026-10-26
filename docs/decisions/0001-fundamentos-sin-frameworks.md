# Decisión 0001 — Fundamentos explícitos y dependencias pequeñas

**Estado:** aceptada para fases 0 y 1.
**Fecha:** 2026-10-26.
**Documento maestro:** [ROADMAP.md](../../ROADMAP.md).

## Contexto

El objetivo es aprender cómo un modelo solicita herramientas y cómo un programa
controla su ejecución. El entorno objetivo es WSL2 Ubuntu 22.04, Python 3.10 y una
RTX 2060 con 6 GB de VRAM.

## Decisiones

1. Implementar el bucle en Python, sin LangChain ni LangGraph. Esto permite seguir
   los mensajes, los esquemas y las observaciones directamente.
2. Usar la API HTTP nativa de Ollama mediante HTTPX. HTTPX simplifica timeouts,
   errores y simulación del transporte sin ocultar el protocolo en un framework.
3. Usar `jsonschema` para validar esquemas y argumentos. Reimplementar JSON Schema
   añadiría complejidad y errores a una parte que no necesitamos desarrollar desde cero.
4. Declarar un contrato `LLMProvider` con `Protocol`. No se añade herencia ni una
   jerarquía de proveedores antes de necesitarla.
5. Utilizar JSON de configuración con la biblioteca estándar. YAML añadiría otra
   dependencia; TOML no tiene lector estándar en Python 3.10. La estructura prevista
   en el roadmap es orientativa y permite esta adaptación.
6. Conservar solo historial en memoria. SQLite y recuperación entre sesiones
   pertenecen a una fase posterior.
7. Limitar herramientas al workspace y no sobrescribir. Para WSL/Linux se usan
   descriptores y `O_NOFOLLOW` en cada componente de la ruta.
8. Separar pruebas deterministas de una integración real explícita. Los tests del
   motor no deben depender de GPU, latencia ni decisiones variables de un modelo.
9. Añadir solo una CLI mínima para poder comprobar la fase 1. El panel de control
   de la fase 9 no forma parte de este trabajo.
10. Usar `think: true` y muestreo no voraz para la variante instalada. Acotar la
    generación con `num_predict` además del contexto y las rondas. Consultar capacidades
    del modelo al arrancar, sin deducirlas únicamente de su nombre.

## Consecuencias

La implementación se puede leer y depurar sin conocimientos de un framework de agentes.
Hay dos dependencias de ejecución: HTTPX y jsonschema. Se aplica formato y lint con
Ruff y se comprueba comportamiento con Pytest.

No hay planificación independiente, ejecución de comandos, Docker, navegador, memoria
persistente ni coordinación multiagente. El proveedor conserva mensajes en formato
de Ollama; una futura API diferente necesitará un adaptador de mensajes.
