"""Shared git helpers for Idea Forge bare repos and garden worktree."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

GARDEN_SLUG = "seedbank-garden"
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


class GitError(RuntimeError):
    pass


def ensure_dirs(data_dir: Path) -> dict[str, Path]:
    repos = data_dir / "repos"
    garden = data_dir / "garden"
    ssh = data_dir / "ssh"
    tmp = data_dir / "tmp"
    for path in (repos, garden, ssh, tmp):
        path.mkdir(parents=True, exist_ok=True)
    return {"repos": repos, "garden": garden, "ssh": ssh, "tmp": tmp}


def git_available() -> bool:
    return shutil.which("git") is not None


def run_git(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    check: bool = True,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    full_env = os.environ.copy()
    full_env.setdefault("GIT_AUTHOR_NAME", "Idea Forge")
    full_env.setdefault("GIT_AUTHOR_EMAIL", "seedbank@localhost")
    full_env.setdefault("GIT_COMMITTER_NAME", "Idea Forge")
    full_env.setdefault("GIT_COMMITTER_EMAIL", "seedbank@localhost")
    if env:
        full_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        input=input_text,
        text=True,
        capture_output=True,
        env=full_env,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitError(
            result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed"
        )
    return result


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:64] or "repo"


def validate_slug(slug: str) -> bool:
    return bool(SLUG_RE.match(slug)) and slug != GARDEN_SLUG


def repo_path(repos_dir: Path, slug: str) -> Path:
    if ".." in slug or "/" in slug or "\\" in slug:
        raise GitError("Invalid repository slug")
    return repos_dir / f"{slug}.git"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> tuple[str, str, str]:
    """Return (full_token, prefix, hash)."""
    token = "sb_" + secrets.token_urlsafe(32)
    return token, token[:10], hash_token(token)


def ssh_fingerprint(public_key: str) -> str:
    parts = public_key.strip().split()
    if len(parts) < 2:
        raise GitError("Invalid SSH public key")
    import base64

    try:
        key_bytes = base64.b64decode(parts[1])
    except Exception as exc:  # noqa: BLE001
        raise GitError("Invalid SSH public key encoding") from exc
    digest = hashlib.sha256(key_bytes).digest()
    b64 = base64.b64encode(digest).decode("ascii").rstrip("=")
    return f"SHA256:{b64}"


def init_bare_repo(path: Path, *, default_branch: str = "main") -> None:
    if path.exists():
        raise GitError(f"Repository already exists: {path.name}")
    path.mkdir(parents=True, exist_ok=False)
    run_git(["init", "--bare", "-b", default_branch, str(path)])
    run_git(["config", "http.receivepack", "true"], cwd=path)
    run_git(["config", "receive.denyCurrentBranch", "ignore"], cwd=path)


def seed_initial_commit(bare: Path, *, default_branch: str, readme: str) -> None:
    with tempfile.TemporaryDirectory(prefix="seedbank-init-") as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        run_git(["init", "-b", default_branch], cwd=repo)
        (repo / "README.md").write_text(readme, encoding="utf-8")
        run_git(["add", "README.md"], cwd=repo)
        run_git(["commit", "-m", "Initial commit"], cwd=repo)
        run_git(["remote", "add", "origin", str(bare)], cwd=repo)
        run_git(["push", "-u", "origin", default_branch], cwd=repo)


def ensure_garden(repos_dir: Path, garden_dir: Path) -> Path:
    bare = repos_dir / f"{GARDEN_SLUG}.git"
    if not bare.exists():
        init_bare_repo(bare, default_branch="main")
        seed_initial_commit(
            bare,
            default_branch="main",
            readme="# Idea Forge garden\n\nAuto-versioned entries. Fetch-only.\n",
        )
        run_git(["config", "http.receivepack", "false"], cwd=bare)

    git_meta = garden_dir / ".git"
    if not git_meta.exists():
        garden_dir.mkdir(parents=True, exist_ok=True)
        # Ignore placeholder keep files when deciding if the dir is "empty"
        meaningful = [
            p for p in garden_dir.iterdir() if p.name not in {".gitkeep", ".git"}
        ]
        if meaningful:
            with tempfile.TemporaryDirectory(prefix="seedbank-garden-clone-") as tmp:
                tmp_path = Path(tmp) / "garden"
                run_git(["clone", str(bare), str(tmp_path)])
                if not git_meta.exists():
                    shutil.move(str(tmp_path / ".git"), str(git_meta))
                # Bring in README from clone if missing
                for item in tmp_path.iterdir():
                    if item.name == ".git":
                        continue
                    dest = garden_dir / item.name
                    if not dest.exists():
                        shutil.move(str(item), str(dest))
        else:
            # Remove keepers so git clone can use the directory
            for keeper in garden_dir.glob(".gitkeep"):
                keeper.unlink(missing_ok=True)
            run_git(["clone", str(bare), str(garden_dir)])
    return bare

def list_branches(bare: Path) -> list[str]:
    result = run_git(
        ["for-each-ref", "--format=%(refname:short)", "refs/heads"],
        cwd=bare,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def list_tags(bare: Path) -> list[str]:
    result = run_git(
        ["for-each-ref", "--format=%(refname:short)", "refs/tags"],
        cwd=bare,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def rev_parse(bare: Path, ref: str) -> str:
    result = run_git(["rev-parse", "--verify", ref], cwd=bare)
    return result.stdout.strip()


def resolve_ref(bare: Path, ref: str) -> str:
    # Accept branch, tag, or full/short sha
    candidates = [ref, f"refs/heads/{ref}", f"refs/tags/{ref}"]
    for candidate in candidates:
        result = run_git(["rev-parse", "--verify", candidate], cwd=bare, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    raise GitError(f"Unknown ref: {ref}")


def ls_tree(bare: Path, ref: str, path: str = "") -> list[dict]:
    rev = resolve_ref(bare, ref)
    spec = rev if not path else f"{rev}:{path}"
    result = run_git(["ls-tree", "-z", spec], cwd=bare)
    entries: list[dict] = []
    for item in result.stdout.split("\0"):
        if not item.strip():
            continue
        meta, name = item.split("\t", 1)
        mode, obj_type, oid = meta.split()
        entries.append(
            {
                "mode": mode,
                "type": obj_type,
                "oid": oid,
                "name": name.split("/")[-1] if "/" in name else name,
                "path": name if not path else f"{path.rstrip('/')}/{name.split('/')[-1]}",
            }
        )
    entries.sort(key=lambda e: (0 if e["type"] == "tree" else 1, e["name"].lower()))
    return entries


def cat_file(bare: Path, ref: str, path: str, *, max_bytes: int = 1_000_000) -> dict:
    rev = resolve_ref(bare, ref)
    result = run_git(["cat-file", "-s", f"{rev}:{path}"], cwd=bare)
    size = int(result.stdout.strip())
    type_result = run_git(["cat-file", "-t", f"{rev}:{path}"], cwd=bare)
    obj_type = type_result.stdout.strip()
    if obj_type != "blob":
        raise GitError("Not a file")
    if size > max_bytes:
        return {"size": size, "binary": True, "truncated": True, "content": None, "text": False}
    raw = subprocess.run(
        ["git", "cat-file", "blob", f"{rev}:{path}"],
        cwd=str(bare),
        capture_output=True,
        check=True,
    ).stdout
    binary = b"\0" in raw
    if binary:
        return {"size": size, "binary": True, "truncated": False, "content": None, "text": False}
    text = raw.decode("utf-8", errors="replace")
    return {"size": size, "binary": False, "truncated": False, "content": text, "text": True}


def log_commits(bare: Path, ref: str, *, path: str | None = None, limit: int = 50) -> list[dict]:
    # Allow rev ranges like main..feature without resolving as a single ref
    if ".." in ref or ref.startswith(("^", "@{")):
        rev = ref
    else:
        rev = resolve_ref(bare, ref)
    args = [
        "log",
        f"-n{limit}",
        "--format=%H%x09%h%x09%an%x09%ae%x09%cI%x09%s",
        rev,
    ]
    if path:
        args.extend(["--", path])
    result = run_git(args, cwd=bare, check=False)
    if result.returncode != 0:
        return []
    commits = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 5)
        if len(parts) < 6:
            continue
        commits.append(
            {
                "sha": parts[0],
                "short": parts[1],
                "author": parts[2],
                "email": parts[3],
                "date": parts[4],
                "subject": parts[5],
            }
        )
    return commits


def show_commit(bare: Path, sha: str) -> dict:
    meta = run_git(
        ["show", "-s", "--format=%H%x09%h%x09%an%x09%ae%x09%cI%x09%s%x09%b", sha],
        cwd=bare,
    )
    parts = meta.stdout.split("\t", 6)
    diff = run_git(["show", "--format=", "--patch", sha], cwd=bare, check=False)
    return {
        "sha": parts[0],
        "short": parts[1],
        "author": parts[2],
        "email": parts[3],
        "date": parts[4],
        "subject": parts[5],
        "body": parts[6].strip() if len(parts) > 6 else "",
        "diff": diff.stdout,
    }


def diff_stat(bare: Path, target: str, source: str) -> str:
    result = run_git(
        ["diff", "--stat", f"{target}...{source}"],
        cwd=bare,
        check=False,
    )
    return result.stdout


def diff_patch(bare: Path, target: str, source: str) -> str:
    result = run_git(
        ["diff", f"{target}...{source}"],
        cwd=bare,
        check=False,
    )
    return result.stdout


def commits_between(bare: Path, target: str, source: str) -> list[dict]:
    return log_commits(bare, f"{target}..{source}", limit=200)


def merge_tree_check(bare: Path, target: str, source: str) -> tuple[bool, str]:
    """Return (can_merge, message)."""
    return merge_worktree_check(bare, target, source)


def merge_worktree_check(bare: Path, target: str, source: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="seedbank-merge-check-") as tmp:
        work = Path(tmp) / "wt"
        run_git(["worktree", "add", "--detach", str(work), f"refs/heads/{target}"], cwd=bare)
        try:
            result = run_git(
                ["merge", "--no-commit", "--no-ff", f"refs/heads/{source}"],
                cwd=work,
                check=False,
            )
            if result.returncode != 0:
                return False, result.stderr.strip() or result.stdout.strip() or "Merge conflicts"
            return True, "OK"
        finally:
            run_git(["merge", "--abort"], cwd=work, check=False)
            run_git(["worktree", "remove", "--force", str(work)], cwd=bare, check=False)


def merge_branches(
    bare: Path,
    *,
    target: str,
    source: str,
    message: str,
) -> str:
    with tempfile.TemporaryDirectory(prefix="seedbank-merge-") as tmp:
        work = Path(tmp) / "wt"
        run_git(
            ["worktree", "add", "-B", target, str(work), f"refs/heads/{target}"],
            cwd=bare,
        )
        try:
            result = run_git(
                ["merge", "--no-ff", f"refs/heads/{source}", "-m", message],
                cwd=work,
                check=False,
            )
            if result.returncode != 0:
                run_git(["merge", "--abort"], cwd=work, check=False)
                raise GitError(result.stderr.strip() or result.stdout.strip() or "Merge failed")
            return run_git(["rev-parse", "HEAD"], cwd=work).stdout.strip()
        finally:
            run_git(["worktree", "remove", "--force", str(work)], cwd=bare, check=False)


def delete_bare_repo(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
