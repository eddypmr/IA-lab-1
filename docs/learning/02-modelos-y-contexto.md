# 02 — LLM, tokens, contexto y system prompts

[Índice](../README.md) · [Tool calling](03-tool-calling.md)

## Qué hace un LLM

Un modelo de lenguaje genera una continuación a partir del contexto recibido. Sus
pesos contienen patrones aprendidos durante el entrenamiento. El modelo no conoce
automáticamente los archivos actuales de tu equipo ni ejecuta Python por describirlo.

Ollama sirve el modelo local y expone una API HTTP. Nuestro proveedor envía mensajes
a esa API y recibe texto o solicitudes de herramientas. Esto separa inferencia y acciones.

## Tokens

Los tokens son fragmentos de texto que usa el modelo. No equivalen siempre a palabras:
la segmentación depende del tokenizer, el idioma y el contenido. Un texto con código
o símbolos puede consumir una cantidad distinta de tokens que otro de longitud similar.

Los 4B del nombre Qwen3 4B aluden aproximadamente a cuatro mil millones de parámetros,
no a la cantidad de tokens de una conversación. La cuantización Q4_K_M reduce el tamaño
de los pesos. Pesos, buffers y caché del contexto también consumen memoria.

## Ventana de contexto

El modelo trabaja con una cantidad limitada de tokens. En esta implementación se
solicitan 8192 mediante `num_ctx`. Comparten ese presupuesto las instrucciones, el
historial, las definiciones de herramientas, las observaciones y la generación.

Una ventana mayor puede aumentar el consumo de memoria. En una RTX 2060 de 6 GB se
parte de un valor moderado y se mide antes de aumentarlo. Tener 32 GB de RAM no implica
tener 32 GB de VRAM. WSL también puede tener asignado un límite de RAM menor que el
total físico de Windows.

El historial de Python puede crecer aunque el modelo solo procese una ventana finita.
Actualmente no hay conteo preventivo de tokens, resúmenes ni recorte controlado.
`/reset` empieza una conversación nueva cuando el contexto crece demasiado. La gestión
avanzada del contexto se abordará con la memoria de la fase correspondiente.

## Roles y system prompt

| Rol | Uso en el laboratorio |
|---|---|
| `system` | Instrucciones de funcionamiento y capacidades. |
| `user` | Objetivo del usuario. |
| `assistant` | Respuesta o petición de herramientas del modelo. |
| `tool` | Observación real de una función Python. |

El system prompt indica que deben ejecutarse herramientas para crear y verificar
archivos. Puede personalizarse con `--system-prompt-file` o `system_prompt` en el JSON.
Son instrucciones para el modelo, no permisos del sistema operativo. Los límites de
archivos se comprueban en Python aunque el modelo solicite otra cosa.

## Muestreo y variantes del mismo nombre

El valor de temperatura no garantiza corrección ni convierte la inferencia en una
prueba determinista. Para este modelo se parte de `temperature: 0.6`, `top_p: 0.95`
y `top_k: 20`, evitando la decodificación voraz. Es el muestreo que recomienda Qwen
para el modo con razonamiento. [Guía oficial de Qwen](https://qwen.readthedocs.io/en/stable/getting_started/quickstart.html).

El alias `qwen3:4b` no basta para conocer todas las capacidades de la descarga actual.
Al inspeccionar `/api/show`, la instalada respondió `thinking.values: [true]`: no es
válido asumir que acepta `think: false`. Por eso se usa `think: true` y la CLI valida
esa configuración antes de empezar. En versiones que no publican esos metadatos,
la comprobación no puede anticipar esta incompatibilidad.

`num_predict: 4096` limita los tokens generados en cada petición, incluido el
razonamiento. Es distinto de `num_ctx` y de `max_iterations`: uno limita la generación,
otro la ventana y otro la cantidad de inferencias. Si se agota la generación, el
proveedor rechaza la respuesta incompleta antes de ejecutar herramientas.

En los experimentos se partió de 4096 tokens de contexto y se probó un límite de
generación de 2048. La tarea completa agotó ese presupuesto. Se amplió el contexto
a 8192 y la generación a 4096 para la variante instalada. La elección se basa en
pruebas del hardware y del modelo, y permanece configurable.

Referencia de los campos HTTP: [API de chat de Ollama](https://docs.ollama.com/api/chat).
