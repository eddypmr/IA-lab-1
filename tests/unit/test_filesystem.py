import os
from datetime import datetime
from pathlib import Path

import pytest

from ai_agent_lab.tools.filesystem import (
    MAX_FILE_BYTES,
    Workspace,
    obtener_fecha,
    register_default_tools,
)
from ai_agent_lab.tools.registry import ToolError


def test_create_read_and_list_utf8(workspace: Workspace) -> None:
    result = workspace.crear_archivo("python.txt", "¡Hola, Python!\n")
    assert result == {"ruta": "python.txt", "bytes": len("¡Hola, Python!\n".encode())}
    assert workspace.leer_archivo("python.txt")["contenido"] == "¡Hola, Python!\n"
    assert workspace.listar_archivos()["archivos"] == ["python.txt"]
    assert (workspace.root / "python.txt").stat().st_mode & 0o777 == 0o600


def test_operations_in_existing_subdirectory(workspace: Workspace) -> None:
    (workspace.root / "notas").mkdir()
    workspace.crear_archivo("notas/a.txt", "abc")
    assert workspace.listar_archivos()["archivos"] == ["notas/"]
    assert workspace.listar_archivos("notas")["archivos"] == ["a.txt"]
    assert workspace.leer_archivo("notas/a.txt")["contenido"] == "abc"


def test_never_overwrites_existing_file(workspace: Workspace) -> None:
    workspace.crear_archivo("a.txt", "original")
    with pytest.raises(ToolError, match="ya existe"):
        workspace.crear_archivo("a.txt", "nuevo")
    assert workspace.leer_archivo("a.txt")["contenido"] == "original"


@pytest.mark.parametrize(
    "ruta", ["../secret", "a/../../secret", "/etc/passwd", "C:/secret", "a\\b", "", "a\x00b"]
)
@pytest.mark.parametrize("operation", ["leer_archivo", "crear_archivo", "listar_archivos"])
def test_rejects_paths_outside_workspace(workspace: Workspace, ruta: str, operation: str) -> None:
    args = (ruta, "contenido") if operation == "crear_archivo" else (ruta,)
    with pytest.raises(ToolError):
        getattr(workspace, operation)(*args)


def test_symlink_file_cannot_be_read_or_overwritten(workspace: Workspace, tmp_path: Path) -> None:
    outside = tmp_path / "secret.txt"
    outside.write_text("secreto", encoding="utf-8")
    (workspace.root / "link.txt").symlink_to(outside)
    tools = register_default_tools(workspace)
    assert tools.execute("leer_archivo", {"ruta": "link.txt"})["ok"] is False
    assert tools.execute("crear_archivo", {"ruta": "link.txt", "contenido": "oops"})["ok"] is False
    assert outside.read_text(encoding="utf-8") == "secreto"
    assert workspace.listar_archivos()["archivos"] == []


def test_symlink_parent_cannot_escape(workspace: Workspace, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secreto", encoding="utf-8")
    (workspace.root / "link").symlink_to(outside, target_is_directory=True)
    tools = register_default_tools(workspace)
    for name, args in (
        ("leer_archivo", {"ruta": "link/secret.txt"}),
        ("crear_archivo", {"ruta": "link/new.txt", "contenido": "oops"}),
        ("listar_archivos", {"ruta": "link"}),
    ):
        assert tools.execute(name, args)["ok"] is False
    assert not (outside / "new.txt").exists()


def test_workspace_prefix_is_not_authorization(workspace: Workspace, tmp_path: Path) -> None:
    sibling = tmp_path / "workspace-other"
    sibling.mkdir()
    with pytest.raises(ToolError):
        workspace.crear_archivo("../workspace-other/file.txt", "oops")
    assert not (sibling / "file.txt").exists()


def test_rejects_fifo_without_blocking(workspace: Workspace) -> None:
    os.mkfifo(workspace.root / "pipe")
    with pytest.raises(ToolError, match="regulares"):
        workspace.leer_archivo("pipe")


def test_limits_utf8_bytes_before_creating_file(workspace: Workspace) -> None:
    with pytest.raises(ToolError, match="límite"):
        workspace.crear_archivo("huge.txt", "á" * MAX_FILE_BYTES)
    assert not (workspace.root / "huge.txt").exists()


def test_rejects_large_or_non_utf8_reads(workspace: Workspace) -> None:
    (workspace.root / "large").write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    with pytest.raises(ToolError, match="límite"):
        workspace.leer_archivo("large")
    (workspace.root / "binary").write_bytes(b"\xff")
    assert (
        register_default_tools(workspace).execute("leer_archivo", {"ruta": "binary"})["ok"] is False
    )


def test_missing_files_and_directories_are_observations(workspace: Workspace) -> None:
    tools = register_default_tools(workspace)
    assert tools.execute("leer_archivo", {"ruta": "missing"})["ok"] is False
    assert tools.execute("crear_archivo", {"ruta": "missing/a", "contenido": "x"})["ok"] is False
    assert not (workspace.root / "missing").exists()


def test_date_includes_timezone() -> None:
    date = datetime.fromisoformat(obtener_fecha()["fecha"])
    assert date.tzinfo is not None


def test_exposes_only_phase_one_tools(workspace: Workspace) -> None:
    schemas = register_default_tools(workspace).schemas()
    assert {tool["function"]["name"] for tool in schemas} == {
        "obtener_fecha",
        "listar_archivos",
        "leer_archivo",
        "crear_archivo",
    }
