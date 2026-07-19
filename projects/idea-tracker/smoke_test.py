#!/usr/bin/env python3
"""Non-destructive smoke test for Idea Forge (uses a temp data dir)."""

from __future__ import annotations

import base64
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="seedbank-smoke-"))


def main() -> int:
    os.environ["SEEDBANK_DATA"] = str(TMP)
    os.environ["SEEDBANK_SSH"] = "0"
    os.environ["SEEDBANK_ADMIN_PASSWORD"] = "seedbank"
    os.environ.pop("SEEDBANK_AI_MOCK", None)
    sys.path.insert(0, str(ROOT))

    import app as seedbank
    from git_util import run_git

    client = seedbank.app.test_client()

    assert client.post("/login", data={"password": "seedbank"}, follow_redirects=True).status_code == 200

    r = client.post("/capture", data={"title": "Quick idea", "category": "idea"}, follow_redirects=True)
    assert r.status_code == 200 and b"Quick idea" in r.data

    r = client.post("/settings/tokens", data={"name": "smoke"}, follow_redirects=True)
    token = re.search(rb"(sb_[A-Za-z0-9_-]+)", r.data).group(1).decode()

    r = client.post(
        "/repos/new",
        data={"name": "Smoke Repo", "slug": "smoke-repo", "description": "test"},
        follow_redirects=True,
    )
    assert b"Smoke Repo" in r.data
    assert b"README.md" in client.get("/repos/smoke-repo").data

    bare = TMP / "repos" / "smoke-repo.git"
    work = TMP / "work"
    run_git(["clone", str(bare), str(work)])
    (work / "feature.txt").write_text("hi\n", encoding="utf-8")
    run_git(["checkout", "-b", "feature"], cwd=work)
    run_git(["add", "feature.txt"], cwd=work)
    run_git(["commit", "-m", "Add feature"], cwd=work)
    run_git(["push", "-u", "origin", "feature"], cwd=work)

    r = client.post(
        "/repos/smoke-repo/pulls/new",
        data={
            "title": "Add feature",
            "body": "smoke",
            "source_branch": "feature",
            "target_branch": "main",
        },
        follow_redirects=True,
    )
    assert b"Opened pull request" in r.data
    assert b"Ready to merge" in client.get("/repos/smoke-repo/pulls/1").data
    assert b"Merged" in client.post("/repos/smoke-repo/pulls/1/merge", follow_redirects=True).data

    auth = base64.b64encode(f"git:{token}".encode()).decode()
    assert client.get("/git/smoke-repo.git/info/refs?service=git-upload-pack").status_code == 401
    r = client.get(
        "/git/smoke-repo.git/info/refs?service=git-upload-pack",
        headers={"Authorization": f"Basic {auth}"},
    )
    assert r.status_code == 200 and b"git-upload-pack" in r.data

    # pin
    entry_id = 1
    client.post(f"/entry/{entry_id}/pin", follow_redirects=True)
    assert b"Pinned" in client.get("/").data

    # category template on new form
    r = client.get("/new?category=agent_instruction")
    assert b"## Role" in r.data

    # related links
    client.post("/capture", data={"title": "Sibling", "category": "idea"}, follow_redirects=True)
    r = client.post("/entry/1/link", data={"to_id": "2"}, follow_redirects=True)
    assert b"Linked" in r.data or b"Sibling" in r.data
    assert b"Sibling" in client.get("/entry/1").data

    # export
    r = client.get("/export/entries.json")
    assert r.status_code == 200
    assert r.is_json
    assert len(r.get_json()["entries"]) >= 2

    # rename should not leave orphan garden files
    client.post(
        f"/entry/{entry_id}/edit",
        data={
            "title": "Renamed idea",
            "category": "project",
            "status": "active",
            "url": "",
            "tags": "",
            "body": "updated",
        },
        follow_redirects=True,
    )
    garden_files = list((TMP / "garden" / "entries").rglob("1-*.md"))
    assert len(garden_files) == 1, garden_files
    assert "renamed-idea" in garden_files[0].name
    assert "project" in str(garden_files[0])

    # open redirect blocked
    r = client.post("/login?next=//evil.example", data={"password": "seedbank"}, follow_redirects=False)
    assert r.status_code in {302, 303}
    assert "evil.example" not in (r.headers.get("Location") or "")

    # public host never 0.0.0.0
    assert "0.0.0.0" not in client.get("/repos/smoke-repo").data.decode()

    # attachments
    from io import BytesIO
    data = {
        "file": (BytesIO(b"# hello config\nkey: value\n"), "notes.md"),
    }
    r = client.post(
        f"/entry/{entry_id}/attachments",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"notes.md" in r.data
    assert b"added" in r.data
    # insert into notes
    att_id = 1
    r = client.post(
        f"/entry/{entry_id}/attachments/{att_id}/insert",
        follow_redirects=True,
    )
    assert b"Attachment: notes.md" in r.data or b"hello config" in r.data

    # FTS search (attachment name + title)
    r = client.get("/?q=notes.md")
    assert r.status_code == 200
    assert b"Renamed idea" in r.data
    r = client.get("/?q=Renamed")
    assert b"Renamed idea" in r.data

    # collections
    r = client.post(
        "/collections/new",
        data={"name": "Launch stack", "slug": "launch-stack", "description": "smoke"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Launch stack" in client.get("/collections").data
    r = client.post(
        f"/entry/{entry_id}/collections",
        data={"collection_id": "1"},
        follow_redirects=True,
    )
    assert b"Added to collection" in r.data or b"Launch stack" in r.data
    assert b"Renamed idea" in client.get("/?collection=launch-stack").data
    assert b"Sibling" not in client.get("/?collection=launch-stack").data

    # JSON import dry-run + apply
    import json

    payload = {
        "entries": [
            {
                "id": 99,
                "title": "Imported seed",
                "category": "idea",
                "status": "active",
                "tags": "import,smoke",
                "body": "from json",
            }
        ],
        "links": [],
        "collections": [
            {"id": 9, "name": "Import stack", "slug": "import-stack", "description": "via import"}
        ],
        "collection_entries": [{"collection_id": 9, "entry_id": 99}],
    }
    raw = json.dumps(payload).encode()
    r = client.post(
        "/import",
        data={"mode": "dry-run", "file": (BytesIO(raw), "export.json")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Dry-run" in r.data
    assert b"Imported seed" in r.data
    r = client.post(
        "/import",
        data={"mode": "apply", "file": (BytesIO(raw), "export.json")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Imported seed" in client.get("/").data
    assert b"Import stack" in client.get("/collections").data
    assert b"Imported seed" in client.get("/?collection=import-stack").data
    assert b"Imported seed" in client.get("/?q=Imported").data

    # AI Assist (mock provider — no network)
    os.environ["SEEDBANK_AI_MOCK"] = "1"
    r = client.post(
        "/settings/ai/openai",
        data={"enabled": "1", "api_key": "sk-test-mock", "make_default": "1"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"ChatGPT" in r.data or b"AI providers" in r.data
    r = client.post("/settings/ai/openai/test", follow_redirects=True)
    assert r.status_code == 200
    assert b"Test OK" in r.data
    for action in ("elaborate", "features", "master_prompt", "scaffold", "deployment"):
        r = client.post(f"/entry/{entry_id}/ai/{action}", follow_redirects=True)
        assert r.status_code == 200
        assert b"Draft" in r.data
        assert b"Mock Assist" in r.data
    r = client.post(
        f"/entry/{entry_id}/ai/apply",
        data={"mode": "append"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Mock Assist" in r.data or b"AI draft applied" in r.data or b"Elaborate" in r.data
    detail = client.get(f"/entry/{entry_id}").data
    assert b"Mock Assist" in detail or b"AI" in detail
    r = client.post(f"/entry/{entry_id}/ai/security", follow_redirects=True)
    assert b"Draft" in r.data or b"Security" in r.data
    client.post(f"/entry/{entry_id}/ai/discard", follow_redirects=True)

    # failed assist call should clear stale draft for this entry
    with client.session_transaction() as sess:
        sess[f"ai_draft_{entry_id}"] = {
            "action": "elaborate",
            "action_label": "Elaborate",
            "provider": "openai",
            "provider_label": "ChatGPT (OpenAI)",
            "draft": "stale draft should disappear on failure",
            "default_apply": "replace",
        }
    os.environ.pop("SEEDBANK_AI_MOCK", None)
    client.post(
        "/settings/ai/openai",
        data={"enabled": "1", "clear_key": "1"},
        follow_redirects=True,
    )
    r = client.post(f"/entry/{entry_id}/ai/elaborate", follow_redirects=True)
    assert b"stale draft should disappear on failure" not in r.data
    with client.session_transaction() as sess:
        assert f"ai_draft_{entry_id}" not in sess
    os.environ["SEEDBANK_AI_MOCK"] = "1"
    client.post(
        "/settings/ai/openai",
        data={"enabled": "1", "api_key": "sk-test-mock", "make_default": "1"},
        follow_redirects=True,
    )

    # assist preview clamp should cap generated draft length at 20k chars
    long_text = "x" * 25000
    clamped = seedbank._clamp_assist_preview(long_text)
    assert len(clamped) == seedbank.ASSIST_PREVIEW_MAX_CHARS
    assert seedbank._clamp_assist_preview("ok") == "ok"

    # AI apply should normalize markdown formatting (headings/lists/code fences)
    with client.session_transaction() as sess:
        sess[f"ai_draft_{entry_id}"] = {
            "action": "features",
            "action_label": "Suggest Features",
            "provider": "openai",
            "provider_label": "ChatGPT (OpenAI)",
            "draft": "##Heading\n1. first\n4. second\n```python\nprint('x')",
            "default_apply": "append",
        }
    r = client.post(
        f"/entry/{entry_id}/ai/apply",
        data={"mode": "append"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    exported = client.get("/export/entries.json").get_json()
    e1 = next(e for e in exported["entries"] if e["id"] == entry_id)
    body = e1["body"]
    assert "# Assist Section (AI-generated)" in body
    assert "generated by AI, which can make mistakes" in body
    assert "## Heading" in body
    assert "1. first\n2. second" in body
    assert "<!-- ASSIST_SECTION_START action=features -->" in body
    assert "<!-- ASSIST_SECTION_END action=features -->" in body
    assert body.count("```") % 2 == 0
    # re-applying same action should replace the existing action block, not append
    with client.session_transaction() as sess:
        sess[f"ai_draft_{entry_id}"] = {
            "action": "features",
            "action_label": "Suggest Features",
            "provider": "openai",
            "provider_label": "ChatGPT (OpenAI)",
            "draft": "## New heading\n1. replacement one\n3. replacement two",
            "default_apply": "append",
        }
    client.post(
        f"/entry/{entry_id}/ai/apply",
        data={"mode": "append"},
        follow_redirects=True,
    )
    exported = client.get("/export/entries.json").get_json()
    e1 = next(e for e in exported["entries"] if e["id"] == entry_id)
    body = e1["body"]
    assert "replacement one" in body
    assert "first" not in body
    assert body.count("## Assist Action: Suggest Features") == 1
    assert body.count("<!-- ASSIST_SECTION_START action=features -->") == 1

    # External tracker IDs
    client.post(
        "/settings/trackers",
        data={
            "ext_jira_url": "https://example.atlassian.net/browse/{id}",
            "ext_bitbucket_url": "https://bitbucket.org/ws/repo/issues/{id}",
            "ext_github_url": "https://github.com/org/repo/issues/{id}",
        },
        follow_redirects=True,
    )
    r = client.post(
        f"/entry/{entry_id}/edit",
        data={
            "title": "Renamed idea",
            "category": "project",
            "status": "active",
            "url": "",
            "tags": "",
            "body": "updated",
            "jira_id": "PROJ-99",
            "bitbucket_id": "42",
            "github_id": "org/repo#7",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Jira PROJ-99" in r.data
    assert b"Bitbucket 42" in r.data
    assert b"GitHub org/repo#7" in r.data
    assert b"example.atlassian.net/browse/PROJ-99" in r.data
    assert b"PROJ-99" in client.get("/?q=PROJ-99").data

    # Filesystem browser
    browse_root = TMP / "browse-root"
    browse_root.mkdir()
    (browse_root / "nested").mkdir()
    (browse_root / "nested" / "app.code-workspace").write_text("{}", encoding="utf-8")
    client.post(
        "/settings/fs-roots",
        data={"fs_browser_roots": str(browse_root)},
        follow_redirects=True,
    )
    r = client.get("/api/fs/roots")
    assert r.status_code == 200 and str(browse_root) in r.get_json()["roots"]
    r = client.get(f"/api/fs/list?path={browse_root}")
    assert r.status_code == 200
    names = [e["name"] for e in r.get_json()["entries"]]
    assert "nested" in names
    r = client.get(f"/api/fs/list?path={browse_root / 'nested'}")
    assert any(e["name"] == "app.code-workspace" for e in r.get_json()["entries"])
    assert client.get("/api/fs/list?path=/etc").status_code == 400
    assert b"Browse" in client.get("/new").data
    assert b"data-theme-toggle" in client.get("/").data or b"theme-toggle" in client.get("/").data

    # AGENTS.md ingest → timestamped, logged, versioned entry
    agents_path = TMP / "AGENTS.md"
    agents_path.write_text(
        "# AGENTS.md\n\n## Test rule\n\n- dry-run by default\n",
        encoding="utf-8",
    )
    r = client.post(
        "/ingest/agents",
        data={"path": str(agents_path)},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"AGENTS.md" in r.data
    assert b"Ingest metadata" in r.data or b"ingested_at" in r.data
    assert b"Test rule" in r.data
    # second ingest creates another entry
    r = client.post(
        "/ingest/agents",
        data={"path": str(agents_path)},
        follow_redirects=True,
    )
    assert r.status_code == 200
    hist = client.get("/?collection=agents-md-history").data
    assert b"AGENTS.md" in hist
    # API with session cookie (already logged in)
    r = client.post(
        "/api/ingest/agents-md",
        json={"path": str(agents_path), "content": "# Via API\n\nrule\n", "filename": "AGENTS.md"},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["entry_id"]
    assert body["garden_versioned"] in {True, False}
    assert b"Via API" in client.get(f"/entry/{body['entry_id']}").data

    # Batch ingest API (used by the Antigravity export plugin): one good
    # file + one empty (invalid) file, expect one success + one reported
    # failure without the whole request failing.
    r = client.post(
        "/api/ingest/agents-md/batch",
        json={
            "files": [
                {"content": "# Global rules\n\nBe helpful.\n", "filename": "GEMINI.md"},
                {"content": "   ", "filename": "empty.md"},
            ]
        },
    )
    assert r.status_code == 200
    batch_body = r.get_json()
    results = batch_body["results"]
    assert len(results) == 2
    assert results[0]["ok"] is True and results[0]["entry_id"]
    assert results[1]["ok"] is False and "empty" in results[1]["error"].lower()
    assert b"Global rules" in client.get(f"/entry/{results[0]['entry_id']}").data

    assert client.get("/").status_code == 200
    home = client.get("/").data
    assert b"Richard Troiano @ 2026" in home
    assert b"extremesarcasm.org" in home

    print("OK: smoke test passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
