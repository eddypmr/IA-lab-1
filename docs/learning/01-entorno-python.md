# 01 — Python, WSL y desarrollo reproducible

[Índice](../README.md) · [Instalación](../../README.md)

## Python de WSL y entorno virtual

WSL ejecuta su propio Linux. Python y los paquetes de Windows no sustituyen a los de
Ubuntu. El proyecto es compatible con Python 3.10, la versión disponible durante la
implementación, para evitar exigir una actualización de Ubuntu 22.04.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -c "import sys; print(sys.executable)"
```

`venv` crea un intérprete aislado para las dependencias del proyecto. La activación
modifica el `PATH` de la terminal; también puede usarse directamente `.venv/bin/python`.
El entorno virtual no es un sandbox para ejecutar código generado.

## Paquete y diseño src

`src/ai_agent_lab/` contiene el paquete importable. `pyproject.toml` declara sus
metadatos, dependencias, herramientas de desarrollo y entrada `ai-agent-lab`.

```bash
python -m pip install -e '.[dev]'
```

`-e` instala el paquete en modo editable: los cambios en `src/` se usan sin reinstalar.
`[dev]` añade Pytest y Ruff. Usar `python -m pip` ayuda a instalar en el mismo intérprete
que después ejecutará el agente. El diseño `src` obliga a instalar el paquete y evita
que las pruebas funcionen únicamente por importar accidentalmente desde la raíz.

`requirements-dev.lock` captura las versiones de las dependencias verificadas.
`pyproject.toml` expresa los rangos compatibles; el lock permite repetir el entorno
de dependencias usado para la validación en Python 3.10.

## Pytest y Ruff

Pytest comprueba comportamiento: resultados, errores, archivos y protocolo. Los
fixtures crean workspaces temporales distintos para cada prueba, sin tocar documentos
personales. La prueba real de Ollama se activa explícitamente y se diferencia de las
pruebas deterministas que no requieren servicio ni GPU.

Ruff detecta errores comunes, ordena imports y aplica formato. El linter ayuda con la
calidad del código; no sustituye una prueba de comportamiento ni un verificador de tipos.

## Git y VS Code

Git se inicializa en la rama `main`. `.gitignore` excluye entornos, cachés y archivos
generados del workspace. `.gitattributes` fija LF para evitar diferencias de saltos de
línea entre Windows y WSL. No se configura una identidad Git global ni se crea un remoto.

### Comprobar VS Code y sus extensiones

La ventana `IAS` ya está conectada a `WSL: Ubuntu-22.04`. La comprobación de solo lectura
fue `code --status`: en `Process` mostró `window [1] (README.md - IAS [WSL: Ubuntu-22.04])`
y en `Remote` mostró `WSL: Ubuntu-22.04` con Linux. No hace falta volver a abrir otra
ventana ni ejecutar `code .` mientras ya estés viendo este proyecto.

Para comprobarlo desde una terminal WSL en el directorio del proyecto:

```bash
code --status
```

En el resultado, confirma que el título de la ventana termina en `[WSL: Ubuntu-22.04]`
y que el apartado `Remote` señala WSL y Linux. También puedes mirar el indicador verde
de la esquina inferior izquierda de VS Code: debe identificar `WSL: Ubuntu-22.04`.

La configuración del repositorio en `.vscode/` elige `.venv/bin/python`, activa Pytest,
recomienda Python y Ruff y ofrece un perfil de depuración. **Recomendar una extensión
no la instala.** Comprobé los paquetes instalados en el lado WSL mediante:

```bash
code --list-extensions --show-versions
```

VS Code indicó `Extensions installed on WSL: Ubuntu-22.04`. Ahora aparecen Python
(`ms-python.python`, versión 2026.10.0) y Ruff (`charliermarsh.ruff`, versión
2026.90.0). VS Code mantiene por separado las extensiones de Windows y WSL.

Abre la paleta de comandos con `Ctrl+Shift+P`, ejecuta **Python: Select Interpreter**
y selecciona `.venv/bin/python` dentro del workspace WSL. La terminal integrada
confirma que el entorno del proyecto funciona:

```bash
python -c "import sys; print(sys.executable)"
```

Debe terminar en `/home/eddy/IAS/.venv/bin/python`. La configuración `.vscode/` deja
este intérprete como valor por defecto. Comprueba también el intérprete que muestra la
barra de estado: una selección previa del usuario puede prevalecer sobre ese valor.
Con WSL y el intérprete activos, Python, Pytest, Ruff y la depuración se ejecutan en Ubuntu.

## Separar configuración y secretos

Se utiliza JSON para no añadir una dependencia YAML ni exigir `tomllib`, que no viene
incluido en Python 3.10. El proyecto no necesita claves de API. No hay carga implícita
de `.env`: la configuración del agente procede del JSON y de los argumentos CLI.
