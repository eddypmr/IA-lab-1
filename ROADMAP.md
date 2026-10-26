# AI Agent Lab
## Roadmap de desarrollo y especificaciones técnicas

**Versión:** 1.1
**Estado:** En desarrollo
**Objetivo:** Construir un agente de inteligencia artificial autónomo, local, modular y extensible.

**Última actualización:** 2026-10-26.
**Alcance autorizado:** fases 0, 1 y 2. No iniciar la fase 3 hasta indicación explícita.

La implementación y las evidencias de estas fases se documentan en
[docs/](docs/README.md). Este archivo sigue siendo el documento maestro.

---

# 1. Visión del proyecto

AI Agent Lab será un entorno experimental para desarrollar y comprender agentes de inteligencia artificial capaces de utilizar herramientas, ejecutar código, gestionar archivos, resolver problemas y completar objetivos de varios pasos.

El sistema utilizará modelos de lenguaje ejecutados localmente mediante Ollama.

El objetivo no es crear simplemente un chatbot, sino desarrollar un sistema capaz de:

- Interpretar instrucciones en lenguaje natural.
- Planificar tareas complejas.
- Seleccionar herramientas.
- Ejecutar acciones.
- Analizar resultados.
- Detectar errores.
- Corregir problemas automáticamente.
- Mantener memoria entre sesiones.
- Consultar información externa.
- Generar y ejecutar código.
- Coordinar diferentes agentes especializados.

El proyecto priorizará el aprendizaje, la modularidad y la experimentación.

## Principios de diseño

1. **Local-first:** ejecutar modelos localmente siempre que sea posible.
2. **Sin APIs de pago:** no depender de servicios comerciales de inferencia.
3. **Modularidad:** permitir sustituir modelos, herramientas y componentes.
4. **Autonomía configurable:** minimizar las confirmaciones innecesarias.
5. **Observabilidad:** registrar las decisiones y acciones del agente.
6. **Extensibilidad:** facilitar la incorporación de nuevas capacidades.
7. **Seguridad por aislamiento:** ejecutar código generado dentro de entornos controlados.
8. **Aprendizaje:** documentar la arquitectura y las decisiones técnicas.

---

# 2. Entorno de desarrollo

## Hardware

| Componente | Especificación |
|---|---|
| Sistema principal | Windows 11 |
| Entorno Linux | WSL2 Ubuntu 22.04 |
| CPU | Por determinar |
| RAM | 32 GB |
| GPU | NVIDIA RTX 2060 Laptop |
| VRAM | 6 GB |
| CUDA soportado por driver | 13.4 |

## Software

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal |
| Ollama | Servidor local de inferencia |
| Qwen3 4B | Modelo inicial |
| VS Code | Entorno de desarrollo |
| Codex | Asistente de programación |
| Docker | Ejecución aislada |
| SQLite | Memoria persistente |
| Playwright | Automatización web |
| Pytest | Pruebas automatizadas |
| Obsidian | Documentación |

## Estado actual

- [x] WSL2 instalado.
- [x] Ubuntu 22.04 funcionando.
- [x] GPU NVIDIA detectada desde WSL2.
- [x] Ollama instalado.
- [x] Qwen3 4B descargado.
- [x] Modelo ejecutándose al 100 % en GPU.
- [x] Proyecto Python inicializado y validado.
- [x] Primer agente con herramientas implementado.

**Entorno observado durante la implementación (2026-10-26):** Python 3.10.12,
Ollama 0.40.11 y `qwen3:4b` Q4_K_M disponibles. La versión de Ollama difiere de la
0.14.11 indicada inicialmente; no se ha modificado su instalación. El modelo se
ha observado con 8192 tokens de contexto, unos 3,9 GB y 100 % GPU en `ollama ps`.
La descarga declara `thinking.values: [true]`; la configuración utiliza ese modo.

El entorno virtual de Python debe crearse dentro de WSL2. No se debe asumir que la instalación de Python de Windows está disponible dentro de Ubuntu.

---

# 3. Arquitectura general

```text
                         USUARIO
                            |
                            v
                    INTERFAZ DEL AGENTE
                            |
                            v
                    AGENT CONTROLLER
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
          PLANNER        MEMORY        TOOL MANAGER
              |             |             |
              +-------------+-------------+
                            |
                            v
                       LOCAL LLM
                       Ollama
                            |
                            v
                     ACTION ENGINE
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
      FILESYSTEM         TERMINAL          BROWSER
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                     RESULT VALIDATOR
                            |
                   +--------+--------+
                   |                 |
                SUCCESS            FAILURE
                   |                 |
                   v                 v
                FINISH             RETRY
```

## Componentes principales

### Agent Controller

Responsable de coordinar la ejecución del agente.

### LLM Provider

Interfaz de comunicación con Ollama y futuros modelos compatibles.

### Planner

Descompone objetivos complejos en tareas ejecutables.

### Tool Manager

Registra, valida y ejecuta las herramientas disponibles.

### Memory Manager

Gestiona el historial, los resultados y la memoria persistente.

### Action Engine

Ejecuta acciones autorizadas en el entorno correspondiente.

### Result Validator

Comprueba los resultados y determina si se necesita otra acción.

---

# 4. Roadmap de desarrollo

## FASE 0 — Preparación del entorno

**Estado: implementación comprobada desde WSL2; Python y Ruff instaladas en la ventana actual.**

La ventana activa `IAS` está conectada a `WSL: Ubuntu-22.04`, verificado con `code --status`.
`code --list-extensions --show-versions` confirma que Python y Ruff están instaladas.

### Objetivos

Preparar una estructura reproducible de desarrollo.

### Tareas

- [x] Configurar WSL2.
- [x] Verificar NVIDIA y CUDA.
- [x] Instalar Ollama.
- [x] Descargar Qwen3 4B.
- [x] Verificar inferencia en GPU.
- [x] Crear repositorio Git (rama `main`, sin remoto ni commit inicial).
- [x] Crear entorno virtual Python (`.venv/`).
- [x] Preparar configuración de VS Code para WSL, intérprete, Pytest, Ruff y depuración.
- [x] Verificar la conexión de la ventana a WSL con `code --status`.
- [x] Comprobar las extensiones instaladas en WSL con `code --list-extensions`.
- [x] Instalar y verificar Python (`ms-python.python`) y Ruff (`charliermarsh.ruff`) en WSL.
- [x] Configurar Pytest, Ruff y Git (`.gitignore` y finales de línea LF).
- [x] Crear estructura inicial y `pyproject.toml` con compatibilidad Python 3.10.
- [x] Crear README con instalación, CLI, configuración y pruebas.
- [x] Crear documentación técnica y de aprendizaje compatible con Obsidian.
- [x] Registrar versiones verificadas en `requirements-dev.lock`.

### Entregable

Proyecto inicial reproducible con dependencias y configuración documentadas.

### Criterio de aceptación

El proyecto puede instalarse y ejecutarse desde una terminal WSL2.

- [x] Instalación editable en `.venv/`, CLI y comprobación de dependencias verificadas.

---

## FASE 1 — Motor LLM y Tool Calling

**Prioridad: crítica**

**Estado: completada y validada con `qwen3:4b` local.**

Evidencias y comandos en el [informe de validación](docs/experiments/phase-0-1-validation.md).

### Objetivo

Construir un agente capaz de comunicarse con Ollama y ejecutar herramientas Python.

### Funcionalidades

- [x] Comunicación HTTP nativa con Ollama mediante HTTPX.
- [x] Historial conversacional en memoria y `/reset`.
- [x] System prompts configurables por JSON o archivo UTF-8.
- [x] Registro dinámico de herramientas Python de confianza.
- [x] Interpretación de llamadas a funciones nativas de Ollama.
- [x] Validación JSON Schema y ejecución de herramientas registradas.
- [x] Devolución de resultados JSON y errores al modelo como mensajes `tool`.
- [x] Gestión de errores de argumentos, archivos, HTTP y respuestas incompletas.
- [x] Límite configurable de inferencias y de herramientas por respuesta.
- [x] CLI interactiva y modo de tarea única con `--prompt`.
- [x] Contexto, modelo, host y timeout configurables.
- [x] Generación acotada por `num_predict` y validación de controles `think` publicados.
- [x] Pruebas unitarias y aceptación determinista sin GPU.
- [x] Prueba de aceptación opcional contra Ollama local.

### Herramientas iniciales

```python
obtener_fecha()
listar_archivos()
leer_archivo(ruta)
crear_archivo(ruta, contenido)
```

Todas las operaciones de archivos deben estar limitadas al workspace autorizado.

La implementación rechaza rutas de escape y symlinks mediante descriptores POSIX.
`crear_archivo` no sobrescribe; los directorios padres deben existir. Se limita cada
archivo a 64 KiB UTF-8 y cada listado a 200 entradas. No se ejecutan comandos ni código.
La configuración usa `configs/default.json` para evitar una dependencia YAML en esta fase.

### Conceptos que aprender

- LLM.
- Tokens.
- Ventana de contexto.
- System prompts.
- Tool calling.
- JSON Schema.
- Bucles de agentes.

### Entregable

Agente conversacional capaz de ejecutar varias herramientas durante una misma tarea.

### Criterio de aceptación

El agente puede crear tres archivos diferentes mediante llamadas a herramientas y comprobar que existen.

- [x] Aceptación determinista: tres creaciones, listado y tres lecturas mediante herramientas.
- [x] Aceptación real con Ollama: las siete operaciones anteriores y respuesta final,
  verificadas en un workspace temporal; duración observada 81,3 segundos.
- [x] 116 pruebas deterministas correctas y una integración real correcta, ejecutada aparte.
- [x] Ruff, comprobación de formato y compatibilidad de dependencias correctos.

---

## FASE 2 — Ejecución de comandos y Docker Sandbox

**Prioridad: crítica**

**Estado: completada y validada en Docker real.**

El usuario autorizó iniciar esta fase el 2026-10-26. Se implementaron el ejecutor,
las herramientas y las pruebas deterministas. El 2026-10-26 se ejecutaron con éxito
las pruebas de contenedor real y la aceptación integrada con Ollama/Qwen3. Véase
[validación fase 2](docs/experiments/phase-2-validation.md).

### Objetivo

Permitir que el agente ejecute comandos y programas de manera autónoma dentro de un entorno aislado.

### Funcionalidades

- [x] Ejecución de comandos como lista argv dentro de Docker.
- [x] Captura limitada de stdout y stderr, códigos de salida y duración.
- [x] Timeouts configurables y parada del contenedor al expirar.
- [x] Ejecución validada de scripts Python del workspace.
- [x] Límites de CPU, memoria, procesos, filesystem, usuario y red.
- [x] Bind mount exclusivo al workspace y eliminación del contenedor al terminar.
- [x] Pruebas deterministas y aceptación real opt-in preparadas.
- [x] Ejecutar pruebas reales en daemon Docker Desktop integrado con WSL.

### Arquitectura

```text
AGENTE
   |
   v
TOOL MANAGER
   |
   v
DOCKER EXECUTOR
   |
   v
CONTENEDOR AISLADO
   |
   +-- Python
   +-- Scripts
   +-- Tests
   +-- Archivos temporales
   |
   v
RESULTADO
```

### Requisitos

- El agente no debe ejecutar comandos arbitrarios directamente en Windows o WSL.
- Utilizar contenedores sin privilegios.
- No montar directorios personales.
- No montar el socket de Docker dentro del contenedor.
- Desactivar la red por defecto.
- Aplicar límites de CPU, RAM y tiempo.
- Ejecutar procesos con usuario no root.
- Permitir únicamente directorios autorizados.

### Entregable

Herramientas `execute_command()` y `execute_python()` basadas en Docker.

### Criterio de aceptación

Validado: el agente generó un script Python, lo ejecutó en Docker y recuperó el resultado.

---

## FASE 3 — Bucle de autonomía

**Prioridad: crítica**

### Objetivo

Transformar el agente en un sistema capaz de completar objetivos de varios pasos.

### Funcionalidades

- Ciclo de planificación y ejecución.
- Selección automática de herramientas.
- Análisis de resultados.
- Reintentos.
- Corrección de errores.
- Detección de tareas completadas.
- Control de iteraciones.
- Cancelación manual.
- Límites de tiempo.

### Ciclo principal

```text
RECEIVE GOAL
     |
     v
ANALYZE
     |
     v
PLAN
     |
     v
SELECT TOOL
     |
     v
EXECUTE
     |
     v
OBSERVE
     |
     v
EVALUATE
     |
     +---- FAILURE ---> REPLAN
     |
     v
SUCCESS
     |
     v
FINISH
```

### Configuración

```yaml
agent:
  max_iterations: 20
  max_retries: 3
  timeout_seconds: 300
  auto_execute: true
  verbose: true
```

`auto_execute` se aplicará únicamente a las herramientas autorizadas dentro del sandbox.

### Entregable

Motor de ejecución autónoma.

### Criterio de aceptación

El agente recibe una tarea, genera código con un error, detecta el fallo durante la ejecución y lo corrige sin intervención manual.

---

## FASE 4 — Memoria persistente

**Prioridad: alta**

### Objetivo

Permitir que el agente conserve información entre ejecuciones.

### Funcionalidades

- Historial de conversaciones.
- Almacenamiento de tareas.
- Registro de acciones.
- Resultados anteriores.
- Recuperación de contexto.
- Resúmenes automáticos.
- Gestión del tamaño del contexto.

### Tecnología

SQLite inicialmente.

### Estructura conceptual

```text
DATABASE
   |
   +-- conversations
   +-- messages
   +-- tasks
   +-- tool_executions
   +-- memories
```

### Conceptos que aprender

- Persistencia.
- Memoria a corto plazo.
- Memoria a largo plazo.
- Recuperación de información.
- Gestión de contexto.

### Entregable

Sistema de memoria persistente.

### Criterio de aceptación

El agente puede recuperar información relevante de una sesión anterior después de reiniciarse.

---

## FASE 5 — Agente programador

**Prioridad: alta**

### Objetivo

Desarrollar un agente especializado en programación.

### Capacidades

- Crear proyectos Python.
- Analizar estructuras de directorios.
- Leer archivos existentes.
- Generar código.
- Modificar código.
- Ejecutar pruebas.
- Detectar errores.
- Corregir errores.
- Refactorizar.
- Generar documentación.

### Herramientas

```python
read_file()
write_file()
edit_file()
list_directory()
execute_python()
run_tests()
```

### Flujo

```text
OBJETIVO
   |
   v
ANALIZAR REQUISITOS
   |
   v
GENERAR ARCHIVOS
   |
   v
EJECUTAR TESTS
   |
   +---- ERROR ---> CORREGIR
   |
   v
VALIDAR RESULTADO
   |
   v
DOCUMENTAR
```

### Entregable

Agente programador autónomo.

### Criterio de aceptación

Crear una aplicación sencilla con FastAPI, generar sus pruebas y ejecutarlas correctamente.

---

## FASE 6 — Navegación web

**Prioridad: media**

### Objetivo

Permitir al agente consultar páginas web e interactuar con navegadores.

### Tecnología

Playwright.

### Capacidades

- Abrir páginas.
- Navegar.
- Extraer texto.
- Buscar información.
- Interactuar con formularios de prueba.
- Descargar archivos autorizados.
- Capturar pantallas.
- Analizar contenido web.

### Requisitos

- Utilizar perfiles de navegador separados.
- Respetar límites de navegación.
- Controlar descargas.
- No ejecutar automáticamente acciones irreversibles.
- Mantener aisladas las credenciales.

### Entregable

Agente capaz de investigar información pública en Internet.

### Criterio de aceptación

Investigar una biblioteca Python, consultar su documentación y generar un ejemplo funcional.

---

## FASE 7 — Planificación avanzada

**Prioridad: media**

### Objetivo

Mejorar la capacidad del agente para resolver tareas complejas.

### Funcionalidades

- Descomposición de objetivos.
- Subtareas.
- Dependencias.
- Seguimiento de progreso.
- Replanificación.
- Priorización.
- Validación de resultados.
- Recuperación de ejecuciones interrumpidas.

### Estructura de tareas

```text
TASK
 |
 +-- SUBTASK 1
 |
 +-- SUBTASK 2
 |      |
 |      +-- STEP A
 |      +-- STEP B
 |
 +-- SUBTASK 3
```

### Entregable

Planificador con seguimiento de estados.

### Criterio de aceptación

El agente completa una tarea compuesta por varias subtareas dependientes y registra su progreso.

---

## FASE 8 — Sistema multiagente

**Prioridad: experimental**

### Objetivo

Permitir que varios agentes especializados colaboren.

### Agentes iniciales

**Planner Agent**

Analiza objetivos y genera planes.

**Developer Agent**

Escribe y modifica código.

**Tester Agent**

Ejecuta pruebas y analiza fallos.

**Reviewer Agent**

Revisa los resultados.

### Arquitectura

```text
                  USER
                   |
                   v
               ORCHESTRATOR
                   |
          +--------+--------+
          |        |        |
          v        v        v
       PLANNER  DEVELOPER  TESTER
          |        |        |
          +--------+--------+
                   |
                   v
                REVIEWER
                   |
                   v
                 RESULT
```

### Consideraciones

Todos los agentes pueden compartir inicialmente el mismo modelo Qwen3 4B, utilizando instrucciones y contextos diferentes.

No es necesario cargar cuatro modelos independientes en memoria.

### Entregable

Sistema multiagente experimental.

### Criterio de aceptación

Varios agentes especializados colaboran para desarrollar y validar un proyecto pequeño.

---

## FASE 9 — Interfaz y monitorización

**Prioridad: media**

### Objetivo

Facilitar la interacción con el agente y observar su funcionamiento.

### Primera versión

Interfaz CLI.

### Segunda versión

Interfaz web local.

Tecnologías candidatas:

- FastAPI.
- WebSockets.
- Interfaz HTML/JavaScript.
- Streamlit como alternativa sencilla.

### Funcionalidades

- Introducir objetivos.
- Consultar tareas activas.
- Visualizar herramientas utilizadas.
- Ver resultados.
- Consultar historial.
- Cancelar ejecuciones.
- Cambiar modelo.
- Modificar configuración.

### Entregable

Panel local de control del agente.

---

## FASE 10 — Evaluación y optimización

**Prioridad: alta**

### Objetivo

Medir el rendimiento y la fiabilidad del sistema.

### Métricas

- Porcentaje de tareas completadas.
- Tiempo medio de ejecución.
- Número de iteraciones.
- Número de llamadas a herramientas.
- Errores por tarea.
- Reintentos.
- Tokens procesados.
- Velocidad de generación.
- Consumo de VRAM.

### Experimentos

Comparar diferentes modelos locales.

Analizar el efecto de:

- Distintos prompts.
- Diferentes límites de contexto.
- Herramientas disponibles.
- Estrategias de planificación.
- Memoria persistente.
- Número máximo de iteraciones.

### Entregable

Suite de evaluación reproducible.

### Criterio de aceptación

Ejecutar un conjunto de tareas de referencia y generar un informe comparativo.

---

# 5. Estructura prevista del repositorio

```text
AI-Agent-Lab/
│
├── src/
│   └── ai_agent_lab/
│       │
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── core/
│       │   ├── agent.py
│       │   ├── controller.py
│       │   ├── planner.py
│       │   └── executor.py
│       │
│       ├── llm/
│       │   ├── base.py
│       │   └── ollama_provider.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── filesystem.py
│       │   ├── terminal.py
│       │   └── browser.py
│       │
│       ├── memory/
│       │   ├── manager.py
│       │   └── sqlite_store.py
│       │
│       ├── sandbox/
│       │   └── docker_executor.py
│       │
│       └── config/
│           └── settings.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
│
├── docs/
│   ├── architecture/
│   ├── learning/
│   ├── experiments/
│   └── decisions/
│
├── workspace/
│
├── docker/
│
├── configs/
│   └── default.yaml
│
├── pyproject.toml
├── .gitignore
├── .env.example
├── README.md
├── AGENTS.md
└── ROADMAP.md
```

La estructura puede evolucionar durante el desarrollo. No es necesario implementar todos los módulos desde el principio.

---

# 6. Requisitos no funcionales

## Rendimiento

El sistema debe funcionar con 32 GB de RAM y una RTX 2060 de 6 GB.

Se utilizará Qwen3 4B como modelo inicial.

El tamaño del contexto debe ser configurable para controlar el consumo de VRAM.

## Mantenibilidad

- Utilizar tipado de Python.
- Separar responsabilidades.
- Evitar módulos excesivamente grandes.
- Mantener dependencias reducidas.
- Escribir pruebas automatizadas.
- Documentar decisiones arquitectónicas.

## Seguridad operativa

- Separar el proceso del agente del entorno de ejecución.
- Aplicar permisos mínimos.
- Limitar acceso a archivos.
- Evitar exponer credenciales.
- Mantener registros de acciones.
- Permitir detener cualquier ejecución.
- Solicitar confirmación para acciones externas irreversibles.

## Autonomía

El agente debe poder ejecutar secuencias de herramientas autorizadas sin solicitar confirmación en cada paso.

La autonomía debe ser configurable por tipo de herramienta, entorno y nivel de riesgo.

---

# 7. Estrategia de desarrollo

El proyecto debe construirse incrementalmente.

No implementar todas las fases simultáneamente.

Cada fase debe seguir este procedimiento:

1. Revisar los objetivos.
2. Diseñar la solución mínima.
3. Implementar los componentes.
4. Crear pruebas.
5. Ejecutar las pruebas.
6. Corregir los errores.
7. Documentar lo aprendido.
8. Actualizar el roadmap.
9. Continuar con la siguiente fase cuando se cumplan los criterios de aceptación.

No introducir frameworks de agentes como LangChain o LangGraph durante las primeras fases.

Primero se implementarán manualmente los mecanismos fundamentales.

Posteriormente podrán evaluarse esos frameworks para comparar enfoques.

---

# 8. Documentación con Obsidian

La carpeta `docs/` estará organizada mediante archivos Markdown compatibles con Obsidian.

Cada fase debe generar documentación sobre:

- Conceptos aprendidos.
- Arquitectura implementada.
- Decisiones técnicas.
- Problemas encontrados.
- Soluciones aplicadas.
- Experimentos realizados.
- Posibles mejoras.

Utilizar enlaces relativos de Markdown para facilitar la navegación entre documentos.

Mantener los archivos de documentación junto al código permitirá consultar el proyecto desde VS Code y Obsidian.

---

# 9. Instrucciones para Codex

Codex actuará como asistente principal de desarrollo.

Debe respetar las siguientes instrucciones:

1. Leer `README.md`, `ROADMAP.md` y `AGENTS.md` antes de implementar cambios importantes.
2. Seguir las fases del roadmap.
3. No implementar funcionalidades de fases futuras sin necesidad.
4. Priorizar código sencillo, modular y comprensible.
5. Utilizar Python como lenguaje principal.
6. Mantener compatibilidad con WSL2 Ubuntu 22.04.
7. Utilizar Ollama como proveedor inicial.
8. No introducir APIs de pago.
9. Crear pruebas para las funcionalidades implementadas.
10. Ejecutar las pruebas cuando sea posible.
11. Documentar cambios importantes.
12. Actualizar el estado de las tareas completadas.
13. Explicar las decisiones arquitectónicas relevantes.
14. Evitar dependencias innecesarias.
15. No modificar archivos fuera del repositorio sin autorización.
16. Utilizar Docker para ejecutar código generado por el agente.
17. No almacenar secretos en el repositorio.
18. Mantener un registro de limitaciones y problemas pendientes.

## Primera tarea para Codex

**Implementar únicamente la Fase 0 y la Fase 1.**

Antes de escribir código:

- Inspeccionar el repositorio.
- Comprobar el entorno Python.
- Verificar la disponibilidad de Ollama.
- Confirmar que `qwen3:4b` está disponible.
- Identificar dependencias necesarias.

Después:

- Crear la estructura inicial del proyecto.
- Configurar `pyproject.toml`.
- Implementar el proveedor Ollama.
- Implementar el registro de herramientas.
- Implementar las herramientas básicas de archivos.
- Implementar el bucle de tool calling.
- Crear una CLI sencilla.
- Incorporar pruebas unitarias.
- Documentar la instalación y el funcionamiento.

## Resultado esperado

Al finalizar, debe ser posible ejecutar:

```bash
python -m ai_agent_lab.main
```

Y solicitar:

> Crea tres archivos de texto sobre Python, Docker y CUDA. Después comprueba que se han creado correctamente.

El agente deberá utilizar las herramientas necesarias y comunicar los resultados reales de la ejecución.

---

# 10. Definición de éxito del proyecto

El proyecto se considerará funcional cuando un usuario pueda proporcionar un objetivo de programación y el agente sea capaz de:

1. Comprender el objetivo.
2. Crear un plan.
3. Generar los archivos necesarios.
4. Ejecutar código dentro de Docker.
5. Detectar errores.
6. Corregirlos automáticamente.
7. Ejecutar pruebas.
8. Validar el resultado.
9. Documentar las acciones realizadas.
10. Entregar un resumen del trabajo completado.

Todo utilizando modelos locales y sin depender de APIs comerciales de pago.

**Objetivo final: comprender y construir desde cero la arquitectura fundamental de un agente de IA autónomo.**
