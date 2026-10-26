"""Ejecutor Docker con límites explícitos y sin shell en el proceso anfitrión."""

import json
import logging
import os
import signal
import subprocess
import threading
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from ai_agent_lab.config.settings import SandboxSettings
from ai_agent_lab.tools.filesystem import Workspace
from ai_agent_lab.tools.registry import ToolError

logger = logging.getLogger(__name__)


class DockerExecutor:
    def __init__(
        self,
        workspace: Workspace | None,
        settings: SandboxSettings,
        *,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        self.workspace = workspace
        self.settings = settings
        self._popen = popen
        self._run = run

    def _docker(self, *args: str) -> list[str]:
        return [self.settings.docker_executable, *args]

    def check(self) -> dict[str, str]:
        """Comprueba CLI, daemon Linux local y presencia de la imagen sin descargarla."""
        try:
            context = self._run(
                self._docker(
                    "context", "inspect", "--format", '{{(index .Endpoints "docker").Host}}'
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "No encuentro la CLI de Docker en WSL. Activa Docker Desktop para "
                "Ubuntu-22.04 en Settings > Resources > WSL Integration y comprueba `docker info`."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError("Docker no respondió al consultar su contexto.") from exc
        except OSError as exc:
            raise ToolError("No se pudo iniciar la CLI de Docker en WSL.") from exc
        if context.returncode != 0:
            detail = context.stderr.strip()
            raise ToolError(
                "No se pudo consultar Docker Context. Ejecuta `docker info` desde WSL. "
                f"{detail[:400]}"
            )
        endpoint = context.stdout.strip()
        if endpoint.startswith('"'):
            try:
                endpoint = json.loads(endpoint)
            except ValueError as exc:
                raise ToolError("Docker devolvió un endpoint de contexto inválido.") from exc
        if not isinstance(endpoint, str) or not endpoint.startswith(("unix://", "npipe://")):
            raise ToolError(
                "Solo se admiten endpoints Docker locales por socket Unix o Windows; "
                "los endpoints TCP y SSH no pueden montar el workspace local de forma segura."
            )
        try:
            daemon = self._run(
                self._docker("info", "--format", "{{.OSType}} {{.ServerVersion}}"),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
            raise ToolError(
                "Docker Desktop no está ejecutando un daemon local accesible desde WSL. "
                "Inícialo y confirma `docker info` en Ubuntu."
            ) from exc
        if daemon.returncode != 0:
            detail = daemon.stderr.strip()
            raise ToolError(
                f"Docker daemon no disponible. Inicia Docker Desktop y comprueba `docker info`. "
                f"{detail[:400]}"
            )
        parts = daemon.stdout.strip().split(maxsplit=1)
        if len(parts) != 2 or parts[0] != "linux":
            raise ToolError("El sandbox requiere un Docker Engine local de contenedores Linux.")
        try:
            image = self._run(
                self._docker("image", "inspect", "--format", "{{.Id}}", self.settings.image),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
            raise ToolError("No se pudo comprobar la imagen local del sandbox.") from exc
        if image.returncode != 0 or not image.stdout.strip():
            raise ToolError(
                f"La imagen {self.settings.image} no está descargada. Desde WSL, "
                f"ejecuta `docker pull {self.settings.image}`; el agente no descarga imágenes."
            )
        return {
            "server": parts[1],
            "endpoint": endpoint,
            "image": self.settings.image,
        }

    def _build_argv(self, container_name: str, argv: list[str]) -> list[str]:
        if self.workspace is None:
            raise ToolError("El DockerExecutor aún no tiene un workspace asociado.")
        root = self.workspace.root
        if not root.is_absolute():
            raise ToolError("La raíz del workspace debe ser absoluta para montarla en Docker.")
        if ":" in str(root) or "," in str(root):
            raise ToolError("Docker no admite ':' ni ',' en la ruta del workspace.")
        try:
            uid, gid = os.getuid(), os.getgid()
        except AttributeError as exc:
            raise ToolError("DockerExecutor solo admite Linux/WSL.") from exc
        return self._docker(
            "run",
            "--rm",
            "--init",
            "--pull=never",
            "--name",
            container_name,
            "--label",
            "ai-agent-lab.managed=true",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--user",
            f"{uid}:{gid}",
            "--cpus",
            str(self.settings.cpus),
            "--memory",
            f"{self.settings.memory_mb}m",
            "--memory-swap",
            f"{self.settings.memory_mb}m",
            "--pids-limit",
            str(self.settings.pids_limit),
            "--shm-size=16m",
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,nodev,size={self.settings.tmpfs_size_mb}m,mode=1777",
            "--mount",
            f"type=bind,source={root},target=/workspace",
            "--workdir",
            "/workspace",
            "--env",
            "HOME=/tmp",
            "--env",
            "TMPDIR=/tmp",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "--stop-timeout",
            "2",
            self.settings.image,
            *argv,
        )

    def execute(self, argv: list[str]) -> dict[str, object]:
        if not isinstance(argv, list) or not argv:
            raise ToolError("El comando debe ser una lista no vacía de argumentos.")
        if any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv):
            raise ToolError("Cada argumento del comando debe ser un texto no vacío sin NUL.")
        if sum(len(arg.encode("utf-8")) for arg in argv) > 8192 or len(argv) > 128:
            raise ToolError("El comando supera el límite de 128 argumentos o 8192 bytes.")

        name = f"ai-agent-lab-{uuid.uuid4().hex[:16]}"
        command = self._build_argv(name, argv)
        captured = [bytearray(), bytearray()]
        truncated = [False, False]

        def drain(stream: object, index: int) -> None:
            try:
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        return
                    remaining = self.settings.output_limit_bytes - len(captured[index])
                    if remaining > 0:
                        captured[index].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated[index] = True
            except (OSError, ValueError):
                return

        started = time.monotonic()
        try:
            process = self._popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
                start_new_session=True,
                bufsize=0,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "No encuentro la CLI de Docker en WSL. Activa Docker Desktop > Resources > "
                "WSL Integration para Ubuntu-22.04."
            ) from exc
        except (OSError, ValueError) as exc:
            raise ToolError("No se pudo iniciar Docker con el comando solicitado.") from exc

        readers = [
            threading.Thread(target=drain, args=(process.stdout, 0), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, 1), daemon=True),
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            exit_code = process.wait(timeout=self.settings.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._stop_container(name)
            self._stop_docker_client(process)
            exit_code = 124
        except KeyboardInterrupt:
            self._stop_container(name)
            self._stop_docker_client(process)
            raise
        finally:
            for reader in readers:
                reader.join(timeout=2)

        result = {
            "exit_code": exit_code,
            "stdout": bytes(captured[0]).decode("utf-8", errors="replace"),
            "stderr": bytes(captured[1]).decode("utf-8", errors="replace"),
            "timed_out": timed_out,
            "output_truncated": any(truncated),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
        logger.info("Docker command exit=%d timed_out=%s", exit_code, timed_out)
        return result

    def _stop_container(self, name: str) -> None:
        """A timed-out CLI cannot leave its named, labelled container running."""
        try:
            stopped = self._run(
                self._docker("stop", "--time", "2", name),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
                check=False,
            )
            if stopped.returncode == 0:
                return
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            logger.warning("Docker stop failed for sandbox container %s; trying kill", name)
        try:
            killed = self._run(
                self._docker("kill", name),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
            if killed.returncode != 0:
                logger.error("Docker did not confirm killing sandbox container %s", name)
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            logger.error("Docker kill failed for sandbox container %s", name)

    @staticmethod
    def _stop_docker_client(process: subprocess.Popen) -> None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait()

    def execute_python(self, ruta: str, argumentos: list[str] | None = None) -> dict[str, object]:
        if self.workspace is None:
            raise ToolError("El DockerExecutor aún no tiene un workspace asociado.")
        parts = Workspace._parts(ruta)
        if not parts or Path(parts[-1]).suffix != ".py":
            raise ToolError("Indica la ruta relativa de un archivo .py del workspace.")
        try:
            self.workspace.leer_archivo(ruta)
        except (OSError, UnicodeError) as exc:
            raise ToolError(
                "El script debe ser un archivo UTF-8 regular dentro del workspace."
            ) from exc
        if argumentos is None:
            argumentos = []
        if not isinstance(argumentos, list) or any(
            not isinstance(arg, str) or "\x00" in arg or len(arg) > 4096 for arg in argumentos
        ):
            raise ToolError(
                "argumentos debe ser una lista de textos UTF-8 de hasta 4096 caracteres."
            )
        relative_path = "/".join(parts)
        return self.execute(["python", f"/workspace/{relative_path}", *argumentos])
