# 04 — Problemas encontrados, soluciones y límites

[Índice](../README.md) · [Verificación](../experiments/phase-0-1-validation.md)

## Problemas del entorno

| Problema observado | Solución aplicada |
|---|---|
| `git status` fallaba: no había repositorio válido. | Se inicializó Git con rama `main`; el montaje de `.git` requería salir del sandbox. |
| Ollama y NVIDIA no eran accesibles desde el sandbox de la sesión. | Se repitieron las comprobaciones con permisos fuera del sandbox; se confirmó servicio, modelo y GPU. |
| La versión indicada inicialmente era 0.14.11; la comprobación real devolvió 0.40.11. | Se documenta la versión observada, sin modificar la instalación de Ollama. |
| `pip install` falló al resolver PyPI desde el sandbox. | Se repitió la instalación con acceso autorizado a red, dentro de `.venv`. |
| La primera inferencia superó 120 s y generó miles de tokens sin herramientas. | Se inspeccionaron registros, plantilla y `/api/show`: la variante instalada solo permite `think: true`. Se corrigió el modo, se evitó muestreo voraz y se añadió `num_predict` para acotar la generación. |
| Con razonamiento activado, 2048 tokens de generación no bastaron para la tarea completa. | Se rechazó la respuesta truncada sin ejecutar herramientas y se ajustaron los valores iniciales a 8192 de contexto y 4096 de generación. |
| Una tarea manual de crear y ejecutar un script agotó `num_predict=4096`, incluso con timeout HTTP de 300 s. | El agente rechazó la salida truncada y no ejecutó herramientas. Con `--num-ctx 12288 --num-predict 8192 --timeout 300`, Qwen completó la tarea y Docker devolvió 42. En esta GPU de 6 GB, esos valores aumentan memoria y latencia; se mantienen como ajuste opcional, no como valores globales. |
| Un LLM puede emitir herramientas inexistentes, argumentos incorrectos o respuestas incompletas. | Lista explícita, JSON Schema, validación del mensaje HTTP y errores estructurados. |
| Resolver rutas con un prefijo textual puede autorizar rutas vecinas o seguir symlinks. | Se rechazan rutas no relativas y se recorren descriptores con `O_NOFOLLOW`. |
| Leer un FIFO podría bloquear la ejecución. | Apertura no bloqueante y comprobación de archivo regular antes de leer. |

## Límites actuales

- La verificación realizada corresponde a la versión observada de Ollama. El protocolo
  usado también sigue el formato de las versiones anteriores, pero no se ha instalado
  ni probado separadamente Ollama 0.14.11.
- El historial se pierde al salir y puede crecer más que la ventana de contexto.
  `/reset` lo vacía; no hay resúmenes ni recuperación de sesiones.
- La respuesta final sigue siendo texto de un LLM. El prompt exige evidencia, pero
  no garantiza que el modelo siempre la interprete correctamente. Se pueden revisar
  los archivos y los registros de herramientas.
- La prueba real puede variar si cambia el modelo, la plantilla o Ollama. La prueba
  determinista sirve para separar esa variación de un fallo de nuestro código.
- El control de `think` depende de la variante. La CLI comprueba `thinking.values` si
  el servidor lo publica; versiones antiguas pueden no ofrecer esos metadatos.
- Las herramientas no ejecutan código ni comandos. Crear un archivo `.py` no lo ejecuta.
- Los límites del workspace se aplican a las herramientas incluidas, no al proceso
  Python completo. Los handlers añadidos son código de confianza.
- El acceso seguro usa primitivas POSIX de Linux/WSL. Ejecutar este módulo directamente
  con Python de Windows no es el objetivo de estas fases.
- No se crean subdirectorios mediante herramientas ni se sobrescriben archivos. Para
  repetir una demostración se puede elegir un workspace nuevo con `--workspace`.
- El límite de rondas no deshace acciones. El timeout se aplica a cada petición HTTP,
  no a la duración total del objetivo.
- La conexión de la ventana se confirmó con `code --status`; Python y Ruff ya aparecen
  instaladas en WSL. La guía [01-entorno-python](01-entorno-python.md#comprobar-vs-code-y-sus-extensiones)
  explica cómo revisar el intérprete seleccionado en VS Code. La barra de estado muestra
  la selección de la ventana activa.

## Próximos pasos autorizables

La fase 2 comenzará únicamente cuando lo indique el usuario: añadir ejecución de
comandos y programas en Docker con los límites definidos por el roadmap.
