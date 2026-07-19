"""Embedded SSH git server for Idea Forge (asyncssh)."""

from __future__ import annotations

import asyncio
import logging
import re
import threading
from pathlib import Path
from typing import Callable

import asyncssh

from git_util import GARDEN_SLUG

logger = logging.getLogger("seedbank.ssh")

GIT_COMMAND_RE = re.compile(
    r"^(?P<cmd>git-(?:upload|receive)-pack)\s+'?(?P<path>[^']+)'?\s*$"
)


class IdeaForgeSSHServer(asyncssh.SSHServer):
    def __init__(self, key_lookup: Callable[[str], bool]):
        self._key_lookup = key_lookup

    def begin_auth(self, username: str) -> bool:
        return True

    def public_key_auth_supported(self) -> bool:
        return True

    def validate_public_key(self, username: str, key: asyncssh.SSHKey) -> bool:
        try:
            exported = key.export_public_key().decode("utf-8").strip()
        except Exception:  # noqa: BLE001
            return False
        return self._key_lookup(exported)


def _normalize_key_body(public_key: str) -> str:
    parts = public_key.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return public_key.strip()


def make_key_lookup(get_keys: Callable[[], list[str]]) -> Callable[[str], bool]:
    def lookup(exported: str) -> bool:
        needle = _normalize_key_body(exported)
        for stored in get_keys():
            if _normalize_key_body(stored) == needle:
                return True
        return False

    return lookup


def _ensure_host_key(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        key = asyncssh.generate_private_key("ssh-ed25519")
        key.write_private_key(str(path))
        path.chmod(0o600)
    return path


def _parse_git_command(command: str, repos_dir: Path) -> tuple[str, Path] | tuple[None, str]:
    match = GIT_COMMAND_RE.match((command or "").strip())
    if not match:
        return None, "Only git-upload-pack / git-receive-pack are allowed\n"
    git_cmd = match.group("cmd")
    raw_path = match.group("path").strip().strip("'\"")
    raw_path = raw_path.lstrip("/")
    if raw_path.endswith(".git"):
        slug = raw_path[: -len(".git")]
    else:
        slug = raw_path
    if not slug or ".." in slug or "/" in slug or "\\" in slug:
        return None, "Invalid repository path\n"
    if slug == GARDEN_SLUG and git_cmd == "git-receive-pack":
        return None, "Push to seedbank-garden is denied\n"
    bare = repos_dir / f"{slug}.git"
    if not bare.exists():
        return None, f"Repository not found: {slug}\n"
    # Map to `git upload-pack` / `git receive-pack`
    sub = "upload-pack" if git_cmd.endswith("upload-pack") else "receive-pack"
    return sub, bare


async def _pipe(reader, writer) -> None:  # noqa: ANN001
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            if hasattr(writer, "write_eof"):
                writer.write_eof()
            elif hasattr(writer, "close"):
                writer.close()
                if hasattr(writer, "wait_closed"):
                    await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


def build_process_factory(repos_dir: Path):
    async def handle_client(process: asyncssh.SSHServerProcess) -> None:
        command = process.command
        if isinstance(command, bytes):
            command = command.decode("utf-8", errors="replace")
        parsed = _parse_git_command(command or "", repos_dir)
        if parsed[0] is None:
            err = parsed[1]
            process.stderr.write(err.encode("utf-8") if isinstance(err, str) else err)
            process.exit(1)
            return
        sub, bare = parsed
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                sub,
                str(bare),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to start git: {exc}\n".encode()
            process.stderr.write(msg)
            process.exit(1)
            return

        assert proc.stdin and proc.stdout and proc.stderr
        await asyncio.gather(
            _pipe(process.stdin, proc.stdin),
            _pipe(proc.stdout, process.stdout),
            _pipe(proc.stderr, process.stderr),
        )
        process.exit(await proc.wait())

    return handle_client


async def _serve(
    *,
    host: str,
    port: int,
    host_key_path: Path,
    repos_dir: Path,
    key_lookup: Callable[[str], bool],
) -> None:
    _ensure_host_key(host_key_path)

    def server_factory() -> IdeaForgeSSHServer:
        return IdeaForgeSSHServer(key_lookup)

    await asyncssh.create_server(
        server_factory,
        host,
        port,
        server_host_keys=[str(host_key_path)],
        process_factory=build_process_factory(repos_dir),
        encoding=None,
    )
    logger.info("SSH git server listening on %s:%s", host, port)
    await asyncio.Future()


def start_ssh_server_thread(
    *,
    host: str,
    port: int,
    host_key_path: Path,
    repos_dir: Path,
    key_lookup: Callable[[str], bool],
) -> threading.Thread:
    def runner() -> None:
        try:
            asyncio.run(
                _serve(
                    host=host,
                    port=port,
                    host_key_path=host_key_path,
                    repos_dir=repos_dir,
                    key_lookup=key_lookup,
                )
            )
        except OSError as exc:
            logger.error("SSH server failed to start: %s", exc)
        except Exception:  # noqa: BLE001
            logger.exception("SSH server crashed")

    thread = threading.Thread(target=runner, name="seedbank-ssh", daemon=True)
    thread.start()
    return thread
