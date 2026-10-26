"""Acceso al workspace en WSL/Linux mediante descriptores y O_NOFOLLOW."""

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path, PureWindowsPath

from ai_agent_lab.tools.registry import Tool, ToolError, ToolRegistry

MAX_FILE_BYTES = 64 * 1024
MAX_DIRECTORY_ENTRIES = 200
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def obtener_fecha() -> dict[str, str]:
    """Fecha con zona horaria del sistema donde se ejecuta el agente."""
    return {"fecha": datetime.now().astimezone().isoformat(timespec="seconds")}


class Workspace:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.root = root.resolve(strict=True)

    @staticmethod
    def _parts(ruta: str) -> tuple[str, ...]:
        if (
            not isinstance(ruta, str)
            or not ruta.strip()
            or "\x00" in ruta
            or "\\" in ruta
            or Path(ruta).is_absolute()
            or PureWindowsPath(ruta).drive
            or ".." in Path(ruta).parts
        ):
            raise ToolError("Usa una ruta relativa dentro del workspace, sin '..' ni enlaces.")
        return Path(ruta).parts

    @contextmanager
    def _directory(self, parts: tuple[str, ...]) -> Iterator[int]:
        """No seguir symlinks, ni siquiera si cambia un componente durante la operación."""
        descriptor = os.open(self.root, DIRECTORY_FLAGS)
        try:
            for part in parts:
                child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            yield descriptor
        finally:
            os.close(descriptor)

    def listar_archivos(self, ruta: str = ".") -> dict[str, object]:
        parts = self._parts(ruta)
        entries: list[str] = []
        with self._directory(parts) as directory, os.scandir(directory) as scan:
            for entry in scan:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    entries.append(entry.name + "/")
                elif entry.is_file(follow_symlinks=False):
                    entries.append(entry.name)
                if len(entries) > MAX_DIRECTORY_ENTRIES:
                    raise ToolError("Directorio demasiado grande; lista un subdirectorio.")
        return {"ruta": "/".join(parts) or ".", "archivos": sorted(entries)}

    def leer_archivo(self, ruta: str) -> dict[str, str]:
        parts = self._parts(ruta)
        if not parts:
            raise ToolError("Debes indicar un archivo, no el directorio workspace.")
        with self._directory(parts[:-1]) as directory:
            descriptor = os.open(
                parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            with os.fdopen(descriptor, "rb") as file:
                if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                    raise ToolError("Solo se pueden leer archivos regulares.")
                data = file.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ToolError(f"El archivo supera el límite de {MAX_FILE_BYTES} bytes.")
        return {"ruta": "/".join(parts), "contenido": data.decode("utf-8")}

    def crear_archivo(self, ruta: str, contenido: str) -> dict[str, object]:
        parts = self._parts(ruta)
        if not parts:
            raise ToolError("Debes indicar un nombre de archivo.")
        data = contenido.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise ToolError(f"El contenido supera el límite de {MAX_FILE_BYTES} bytes.")
        with self._directory(parts[:-1]) as directory:
            try:
                descriptor = os.open(
                    parts[-1],
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
            except FileExistsError as exc:
                raise ToolError(
                    "El archivo ya existe; crear_archivo no sobrescribe archivos."
                ) from exc
            with os.fdopen(descriptor, "wb") as file:
                file.write(data)
        return {"ruta": "/".join(parts), "bytes": len(data)}


def register_default_tools(workspace: Workspace) -> ToolRegistry:
    registry = ToolRegistry()
    path = {"type": "string", "minLength": 1, "description": "Ruta relativa al workspace."}
    for name, description, properties, required, handler in (
        ("obtener_fecha", "Obtiene la fecha y hora local con zona horaria.", {}, [], obtener_fecha),
        (
            "listar_archivos",
            "Lista archivos y directorios; omite enlaces simbólicos. Por defecto lista '.'.",
            {"ruta": path},
            [],
            workspace.listar_archivos,
        ),
        (
            "leer_archivo",
            "Lee un archivo UTF-8 de hasta 64 KiB dentro del workspace.",
            {"ruta": path},
            ["ruta"],
            workspace.leer_archivo,
        ),
        (
            "crear_archivo",
            "Crea un archivo UTF-8 de hasta 64 KiB. No sobrescribe; el directorio debe existir.",
            {"ruta": path, "contenido": {"type": "string", "maxLength": MAX_FILE_BYTES}},
            ["ruta", "contenido"],
            workspace.crear_archivo,
        ),
    ):
        registry.register(
            Tool(
                name=name,
                description=description,
                parameters={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                handler=handler,
            )
        )
    return registry
