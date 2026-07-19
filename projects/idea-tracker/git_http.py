"""Git Smart HTTP backend (token auth) for Idea Forge."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from flask import Request, Response, request
from werkzeug.datastructures import Headers

from git_util import GARDEN_SLUG, GitError, repo_path


def extract_token(req: Request) -> str | None:
    auth = req.authorization
    if auth and auth.password:
        return auth.password
    if auth and auth.username and not auth.password:
        # allow token as username
        return auth.username
    header = req.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    # git sometimes sends token via query for older clients — ignore
    return None


def run_http_backend(
    *,
    repos_dir: Path,
    slug: str,
    path_info: str,
    req: Request,
    allow_push: bool,
) -> Response:
    bare = repo_path(repos_dir, slug)
    if not bare.exists():
        return Response("Repository not found\n", status=404, mimetype="text/plain")

    if not allow_push and req.method == "POST" and "git-receive-pack" in (
        path_info + "?" + (req.query_string.decode("utf-8", errors="ignore"))
    ):
        return Response("Push denied\n", status=403, mimetype="text/plain")

    # Translate Flask path into CGI PATH_INFO expected by git-http-backend.
    # Request comes in as /git/<slug>.git/<rest>
    cgi_path_info = f"/{slug}.git"
    if path_info:
        cgi_path_info += "/" + path_info.lstrip("/")

    env = os.environ.copy()
    env.update(
        {
            "GIT_PROJECT_ROOT": str(repos_dir),
            "GIT_HTTP_EXPORT_ALL": "1",
            "PATH_INFO": cgi_path_info,
            "REQUEST_METHOD": req.method,
            "QUERY_STRING": req.query_string.decode("utf-8", errors="ignore"),
            "CONTENT_TYPE": req.content_type or "",
            "REMOTE_USER": "seedbank",
            "REMOTE_ADDR": req.remote_addr or "127.0.0.1",
            "SERVER_PROTOCOL": req.environ.get("SERVER_PROTOCOL", "HTTP/1.1"),
        }
    )
    if not allow_push:
        env["GIT_HTTP_RECEIVE_PACK"] = "false"

    content_length = req.content_length
    if content_length is not None:
        env["CONTENT_LENGTH"] = str(content_length)

    body = req.get_data()
    try:
        proc = subprocess.run(
            ["git", "http-backend"],
            input=body,
            capture_output=True,
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError("git binary not found") from exc

    if proc.returncode != 0 and not proc.stdout:
        return Response(
            proc.stderr or b"git http-backend failed\n",
            status=500,
            mimetype="text/plain",
        )

    # CGI response: headers, blank line, body
    raw = proc.stdout
    header_blob, _, rest = raw.partition(b"\r\n\r\n")
    if not rest and b"\n\n" in raw:
        header_blob, _, rest = raw.partition(b"\n\n")

    status = 200
    headers: Headers = Headers()
    for line in header_blob.decode("iso-8859-1", errors="replace").splitlines():
        if not line or ":" not in line:
            if line.lower().startswith("status:"):
                try:
                    status = int(line.split(":", 1)[1].strip().split(" ", 1)[0])
                except ValueError:
                    status = 500
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key.lower() == "status":
            try:
                status = int(value.split(" ", 1)[0])
            except ValueError:
                status = 500
        else:
            headers.add(key, value)

    return Response(rest, status=status, headers=headers)


def is_garden(slug: str) -> bool:
    return slug == GARDEN_SLUG
