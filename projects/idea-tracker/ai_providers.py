"""LLM provider adapters and Assist prompts for Idea Forge."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
from typing import Any, Callable

import requests
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

PROVIDERS: dict[str, dict[str, Any]] = {
    "openai": {
        "label": "ChatGPT (OpenAI)",
        "env_key": "SEEDBANK_OPENAI_API_KEY",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "style": "openai",
    },
    "xai": {
        "label": "Grok (xAI)",
        "env_key": "SEEDBANK_XAI_API_KEY",
        "default_base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-latest",
        "style": "openai",
    },
    "google": {
        "label": "Gemini (Google)",
        "env_key": "SEEDBANK_GOOGLE_API_KEY",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-2.0-flash",
        "style": "google",
    },
    "anthropic": {
        "label": "Claude (Anthropic)",
        "env_key": "SEEDBANK_ANTHROPIC_API_KEY",
        "default_base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-haiku-latest",
        "style": "anthropic",
    },
    "github": {
        "label": "Copilot / GitHub Models",
        "env_key": "SEEDBANK_GITHUB_TOKEN",
        "default_base_url": "https://models.github.ai/inference",
        "default_model": "openai/gpt-4o-mini",
        "style": "openai",
        "auth_header": "Bearer",
        "notes": "Uses a GitHub PAT / Models token — not the VS Code Copilot extension.",
    },
}

ACTIONS: dict[str, dict[str, str]] = {
    "master_prompt": {
        "label": "Master Prompt",
        "default_apply": "append",
        "system": (
            "You create high-quality master prompts for external AI systems. "
            "Use only the provided current-item context. "
            "Do not assume any other project history. "
            "Return only Markdown."
        ),
        "user": (
            "Create a single master prompt from this item that can be copied into "
            "other AI tools.\n\n"
            "Current item context (only):\n"
            "Title: {title}\n"
            "Category: {category}\n"
            "Status: {status}\n"
            "Tags: {tags}\n"
            "URL/Path: {url}\n"
            "Tracker IDs: Jira={jira_id}, Bitbucket={bitbucket_id}, GitHub={github_id}\n"
            "Attachments: {attachments}\n\n"
            "Notes:\n{body}\n\n"
            "Output sections (in order):\n"
            "1) Goal\n"
            "2) Context summary\n"
            "3) Constraints and assumptions\n"
            "4) Available inputs\n"
            "5) Required output format\n"
            "6) Acceptance criteria\n"
            "7) Open questions\n"
            "8) Final Copy/Paste Master Prompt (one block)\n"
        ),
    },
    "format": {
        "label": "Format / restructure",
        "default_apply": "replace",
        "system": (
            "You restructure personal notes into clean Markdown. "
            "Preserve meaning and facts. Use headings, lists, and short paragraphs. "
            "Do not invent new requirements. Return only Markdown."
        ),
        "user": (
            "Restructure these notes for clarity.\n\n"
            "Title: {title}\nCategory: {category}\nTags: {tags}\nURL: {url}\n\n"
            "Notes:\n{body}\n"
        ),
    },
    "elaborate": {
        "label": "Elaborate",
        "default_apply": "replace",
        "system": (
            "You expand sparse personal notes into clearer Markdown with concrete next steps. "
            "Stay grounded in the given content; mark guesses clearly. Return only Markdown."
        ),
        "user": (
            "Elaborate these notes with useful detail and next steps.\n\n"
            "Title: {title}\nCategory: {category}\nTags: {tags}\nURL: {url}\n\n"
            "Notes:\n{body}\n"
        ),
    },
    "features": {
        "label": "Suggest Features",
        "default_apply": "append",
        "system": (
            "You suggest product features from a single item context. "
            "Use only the provided current-item content. "
            "Be concrete and implementation-oriented. "
            "Return only Markdown with a top-level numbered list."
        ),
        "user": (
            "Suggest additional features for this specific item.\n\n"
            "Current item context (only):\n"
            "Title: {title}\n"
            "Category: {category}\n"
            "Status: {status}\n"
            "Tags: {tags}\n"
            "URL/Path: {url}\n"
            "Tracker IDs: Jira={jira_id}, Bitbucket={bitbucket_id}, GitHub={github_id}\n"
            "Attachments: {attachments}\n\n"
            "Notes:\n{body}\n\n"
            "For each feature include:\n"
            "- Feature name\n"
            "- Why it matters\n"
            "- User impact\n"
            "- Technical approach\n"
            "- Complexity (S/M/L)\n"
            "- Risks/dependencies\n"
            "Output requirements:\n"
            "- Generate at least 5 and at most 10 feature suggestions.\n"
            "- Use a top-level numbered list (1., 2., 3., ...).\n"
            "- Group items under Must-have, Should-have, Nice-to-have headings."
        ),
    },
    "scaffold": {
        "label": "Create Scaffold",
        "default_apply": "append",
        "system": (
            "You design implementation scaffolds for software projects. "
            "Use only the provided current-item context. "
            "Return practical Markdown with concrete structure and steps."
        ),
        "user": (
            "Create a scaffold proposal for this item.\n\n"
            "Current item context (only):\n"
            "Title: {title}\n"
            "Category: {category}\n"
            "Status: {status}\n"
            "Tags: {tags}\n"
            "URL/Path: {url}\n"
            "Attachments: {attachments}\n\n"
            "Notes:\n{body}\n\n"
            "Required sections:\n"
            "1) Platform\n"
            "2) OS\n"
            "3) Languages\n"
            "4) Database\n"
            "5) Frontend\n"
            "6) Backend\n"
            "7) System Type\n"
            "8) Recommended repo/folder structure\n"
            "9) Phased build-out checklist\n"
            "10) Key tradeoffs and assumptions"
        ),
    },
    "deployment": {
        "label": "Deployment Script",
        "default_apply": "append",
        "system": (
            "You generate deployment automation guidance and script templates. "
            "Use only the provided current-item context. "
            "Return Markdown only. Prefer safe defaults and clearly mark placeholders."
        ),
        "user": (
            "Generate deployment automation options for this item.\n\n"
            "Current item context (only):\n"
            "Title: {title}\n"
            "Category: {category}\n"
            "Status: {status}\n"
            "Tags: {tags}\n"
            "URL/Path: {url}\n"
            "Attachments: {attachments}\n\n"
            "Notes:\n{body}\n\n"
            "Cover these targets:\n"
            "- Proxmox VM\n"
            "- VMware VM\n"
            "- Container\n"
            "- Azure VM\n"
            "- Amazon EC2\n"
            "- Amazon Container (ECS/Fargate)\n"
            "- VirtualBox\n"
            "- Virt Manager\n\n"
            "Output format:\n"
            "1) Decision matrix (when to pick each)\n"
            "2) Shared prerequisites\n"
            "3) Per-target script template with variables/placeholders\n"
            "4) Validation checklist"
        ),
    },
    "security": {
        "label": "Security check",
        "default_apply": "append",
        "system": (
            "You review plans/notes for security issues. "
            "For each issue give: title, severity (critical/high/medium/low/info), "
            "why it matters, and a suggested fix. Return only Markdown."
        ),
        "user": (
            "Check this entry for security issues and risky assumptions.\n\n"
            "Title: {title}\nCategory: {category}\nTags: {tags}\nURL: {url}\n\n"
            "Notes:\n{body}\n"
            "Attachments: {attachments}\n"
        ),
    },
}

MAX_BODY_CHARS = 12000
REQUEST_TIMEOUT = 60
FEATURE_MIN_SUGGESTIONS = 5
FEATURE_MAX_SUGGESTIONS = 10
FEATURE_NUMBERED_ITEM_RE = re.compile(r"^\d+\.\s+", re.MULTILINE)


class AIError(Exception):
    """User-facing AI failure."""


def fernet_for_secret(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(secret: str, plaintext: str) -> str:
    return fernet_for_secret(secret).encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(secret: str, token: str) -> str:
    try:
        return fernet_for_secret(secret).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError) as exc:
        raise AIError("Stored API key could not be decrypted. Re-save the key.") from exc


def mask_key(key: str | None) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "••••"
    return f"{key[:4]}…{key[-4:]}"


def truncate_body(body: str | None) -> str:
    text = (body or "").strip() or "(empty)"
    if len(text) > MAX_BODY_CHARS:
        return text[:MAX_BODY_CHARS] + "\n\n…[truncated]"
    return text


def build_messages(action: str, entry: dict, attachments: str = "") -> tuple[str, str]:
    spec = ACTIONS.get(action)
    if not spec:
        raise AIError(f"Unknown action: {action}")
    ctx = {
        "title": entry.get("title") or "",
        "category": entry.get("category_label") or entry.get("category") or "",
        "status": entry.get("status_label") or entry.get("status") or "",
        "tags": entry.get("tags") or "",
        "url": entry.get("url") or "",
        "jira_id": entry.get("jira_id") or "(none)",
        "bitbucket_id": entry.get("bitbucket_id") or "(none)",
        "github_id": entry.get("github_id") or "(none)",
        "body": truncate_body(entry.get("body")),
        "attachments": attachments or "(none)",
    }
    return spec["system"], spec["user"].format(**ctx)


def count_feature_suggestions(text: str | None) -> int:
    return len(FEATURE_NUMBERED_ITEM_RE.findall(text or ""))


def _merge_custom_headers(headers: dict, custom_headers_raw: str | None) -> None:
    if not custom_headers_raw:
        return
    try:
        custom = json.loads(custom_headers_raw)
        if isinstance(custom, dict):
            for k, v in custom.items():
                headers[str(k)] = str(v)
    except Exception as e:
        logger.warning("Failed to parse custom headers: %s", e)


def _openai_complete(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    auth_header: str = "Bearer",
    custom_headers: str | None = None,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"{auth_header} {api_key}",
        "Content-Type": "application/json",
    }
    _merge_custom_headers(headers, custom_headers)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    if resp.status_code >= 400:
        raise AIError(f"Provider error ({resp.status_code}): {_safe_err(resp)}")
    data = resp.json()
    try:
        choices = data["choices"]
        choice0 = choices[0]
        message = choice0.get("message") if isinstance(choice0, dict) else None
        if not isinstance(message, dict):
            raise KeyError("message")

        content = message.get("content")
        text = ""
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            # OpenAI-compatible providers may return content as a list of typed
            # parts instead of a single string.
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()

        if text:
            return text

        finish_reason = choice0.get("finish_reason")
        if finish_reason:
            raise AIError(f"Generation stopped prematurely: {finish_reason}")
        raise AIError("Empty output from LLM.")
    except (KeyError, TypeError, IndexError) as exc:
        raise AIError("Unexpected provider response shape.") from exc


def _anthropic_complete(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    custom_headers: str | None = None,
) -> str:
    url = base_url.rstrip("/") + "/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    _merge_custom_headers(headers, custom_headers)
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    if resp.status_code >= 400:
        raise AIError(f"Provider error ({resp.status_code}): {_safe_err(resp)}")
    data = resp.json()
    try:
        parts = data.get("content") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if not text.strip():
            raise KeyError("empty")
        return text.strip()
    except (KeyError, TypeError, AttributeError) as exc:
        raise AIError("Unexpected Anthropic response shape.") from exc


def _google_complete(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    custom_headers: str | None = None,
) -> str:
    url = (
        f"{base_url.rstrip('/')}/models/{model}:generateContent"
        f"?key={api_key}"
    )
    headers = {
        "Content-Type": "application/json",
    }
    _merge_custom_headers(headers, custom_headers)
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    if resp.status_code >= 400:
        raise AIError(f"Provider error ({resp.status_code}): {_safe_err(resp)}")
    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if not text.strip():
            raise KeyError("empty")
        return text.strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIError("Unexpected Gemini response shape.") from exc


def _safe_err(resp: requests.Response) -> str:
    text = (resp.text or "")[:300]
    text = re.sub(r"(sk-|ghp_|xai-|AIza)[A-Za-z0-9_-]+", r"\1…", text)
    return text or resp.reason


def complete(
    provider_key: str,
    *,
    api_key: str,
    base_url: str | None,
    model: str | None,
    system: str,
    user: str,
    max_tokens: int = 1500,
    temperature: float = 0.3,
    custom_headers: str | None = None,
) -> str:
    if os.environ.get("SEEDBANK_AI_MOCK") == "1":
        return (
            f"## Mock Assist ({provider_key})\n\n"
            f"**Action context received.**\n\n"
            f"- System chars: {len(system)}\n"
            f"- User chars: {len(user)}\n\n"
            "This is mock output for tests.\n"
        )

    meta = PROVIDERS.get(provider_key)
    if not meta:
        raise AIError(f"Unknown provider: {provider_key}")
    if not api_key:
        raise AIError(f"{meta['label']} has no API key configured.")

    base = (base_url or meta["default_base_url"]).rstrip("/")
    mdl = model or meta["default_model"]
    style = meta["style"]

    if style == "openai":
        return _openai_complete(
            api_key=api_key,
            base_url=base,
            model=mdl,
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
            auth_header=meta.get("auth_header", "Bearer"),
            custom_headers=custom_headers,
        )
    if style == "anthropic":
        return _anthropic_complete(
            api_key=api_key,
            base_url=base,
            model=mdl,
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
            custom_headers=custom_headers,
        )
    if style == "google":
        return _google_complete(
            api_key=api_key,
            base_url=base,
            model=mdl,
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
            custom_headers=custom_headers,
        )
    raise AIError(f"Unsupported provider style: {style}")


def test_connection(
    provider_key: str,
    *,
    api_key: str,
    base_url: str | None = None,
    model: str | None = None,
    custom_headers: str | None = None,
) -> str:
    return complete(
        provider_key,
        api_key=api_key,
        base_url=base_url,
        model=model,
        system="Reply with exactly: ok",
        user="ping",
        # Some OpenAI-compatible models (including certain Gemini variants)
        # can consume tiny token budgets without emitting visible text.
        max_tokens=64,
        temperature=0,
        custom_headers=custom_headers,
    )
