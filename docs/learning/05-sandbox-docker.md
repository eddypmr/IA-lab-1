# 05 — Ejecutar código dentro de un sandbox Docker

[Índice](../README.md) · [Arquitectura de la fase 2](../architecture/phase-2-docker.md)

## Proceso hijo, contenedor y sistema anfitrión

Un programa lanzado con `subprocess` se convierte en hijo del agente y se ejecuta con
los permisos del usuario WSL. `shell=False` evita que Python interprete una cadena de
texto mediante `/bin/sh`. No crea por sí solo un sandbox: los hijos comparten permisos,
archivos y entorno con el proceso.

Docker arranca un proceso dentro de un contenedor Linux. Una configuración del
contenedor limita su acceso a la red, los archivos y los recursos; Docker Engine crea
y supervisa esa frontera. `subprocess` en el host solo inicia la CLI de Docker. El
código solicitado por el modelo se convierte en argv del proceso **dentro** del
contenedor.

## Lista de argumentos, no shell del host

JSON transporta una cadena de comandos con reglas de quoting ambiguas. Este ejecutor
acepta una lista de argumentos:

```json
{"command": ["python", "-c", "print(19 + 23)"]}
```

Python la entrega al cliente Docker con `shell=False`. Si la tarea necesita tuberías,
`sh -c`, sigue siendo un shell *dentro del contenedor* y no en el anfitrión. Para un
programa guardado en disco, `execute_python` primero valida la ruta relativa y usa
`python /workspace/archivo.py`.

## Controles de recursos

| Control | Valor inicial | Propósito |
|---|---:|---|
| `--network=none` | sin red | Evita conexiones desde el programa dentro del contenedor. |
| `--user` | UID/GID del usuario WSL | No ejecutar el programa como root. |
| `--read-only` | activo | Impedir escribir en el resto del sistema raíz. |
| capabilities | todas retiradas | Reducir operaciones privilegiadas de Linux. |
| `no-new-privileges` | activo | Impedir elevar privilegios desde el proceso. |
| CPU | 1 núcleo | Limitar consumo de CPU. |
| memoria y swap | 512 MiB | Limitar memoria del contenedor. |
| procesos | 64 | Limitar procesos e hilos. |
| `/tmp` | 64 MiB, noexec | Espacio temporal limitado. |
| tiempo | 30 s | Parar la ejecución y devolver código 124. |
| stdout / stderr | 64 KiB cada uno | Respuesta acotada que retorna al modelo. |

Los límites se ajustan con `configs/default.json`, dentro de los rangos validados.
Un timeout de Docker y un límite de ronda del agente significan cosas diferentes:
el primero corta un proceso; el segundo limita cuántas inferencias pide el modelo.

## Docker Desktop y WSL2

La CLI `docker` de WSL y el Docker Engine son componentes distintos. Docker Desktop
puede estar instalado en Windows mientras que su servicio está detenido o su
integración con Ubuntu está desactivada. `docker info` comprueba la comunicación de
la CLI con el daemon.

Se monta un único workspace en `/workspace`; esto permite que un script guarde sus
resultados para inspeccionarlos después. No se monta el socket Docker. El contenedor
se elimina al terminar, pero los cambios escritos en el workspace permanecen.

## Por qué no se descargan imágenes implícitamente

Docker puede descargar una imagen remota cuando falta en el sistema. El agente no debe
iniciar descargas no solicitadas en medio de una tarea. `--pull=never` obliga a preparar
primero la imagen `python:3.10-slim` y permite que `--check` detecte si no está presente.

## Límite del modelo

El modelo propone acciones; ToolRegistry valida sus argumentos y DockerExecutor valida
sus límites. Dentro del contenedor, el programa puede modificar el workspace autorizado.
Eso es parte de la tarea, no una operación reversible. Docker comparte el kernel del
host y el bind mount está diseñado para intercambiar archivos con el contenedor.

[Decisión arquitectónica](../decisions/0002-limites-docker.md) ·
[Verificación](../experiments/phase-2-validation.md)
