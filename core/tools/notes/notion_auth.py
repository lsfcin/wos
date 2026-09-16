# notion_auth.py — Notion's integration-token store, and the instructions a failure prints
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'hooks'))
from platform_law import secure_dir, secure_file

SERVICE = "notion"
INTEGRATIONS = "https://www.notion.so/my-integrations"
CLI = "core/tools/notes/notion"


class AuthMissing(RuntimeError):
    """No usable token. Carries text written for Lucas — relay it unchanged."""


class NotShared(RuntimeError):
    """The token works; the target was never connected to the integration."""


def config_dir() -> pathlib.Path:
    d = pathlib.Path.home() / ".config" / f"workspace-{SERVICE}"
    d.mkdir(parents=True, exist_ok=True)
    # Asked of the boundary, never chmod'd here. On Windows chmod(0o700) accepts the number, returns
    # cleanly and changes nothing about who may enter — a false green on a directory holding a
    # secret, which is worse than no call at all because the caller is told it is protected.
    secure_dir(d)
    return d


def token_path(alias: str) -> pathlib.Path:
    return config_dir() / f"{alias}.token.json"


def save_token(alias: str, token: str) -> pathlib.Path:
    """Store the secret readable by nobody else. This file is the only copy we keep."""
    path = token_path(alias)
    path.write_text(json.dumps({"token": token.strip()}, indent=2) + "\n", encoding='utf-8', newline='\n')
    secure_file(path)
    return path


def load_token(alias: str) -> str:
    path = token_path(alias)
    token = ""
    if path.exists():
        token = json.loads(path.read_text(encoding='utf-8')).get("token", "").strip()
    if not token:
        raise AuthMissing(setup_text(alias))
    return token


def _store_step(alias: str) -> list:
    """The agent's half, spelled out. A builtin pipe keeps the secret out of argv."""
    return [
        "AGENT: the rest is yours — never hand Lucas a command to type. Take the value he",
        "pastes into the conversation and store it through stdin, not as an argument:",
        f"    printf '%s\\n' '<secret>' | {CLI} auth {alias}",
        f"It lands at {token_path(alias)}, mode 600. `printf` is a shell builtin, so the secret",
        "never appears in any process's argv.",
    ]


def setup_text(alias: str) -> str:
    """Two clicks are Lucas's because they happen inside Notion. Everything else is the agent's."""
    return "\n".join([
        f"NOTION TOKEN MISSING — workspace '{alias}'.",
        "Notion has no headless consent flow, so two things need Lucas's own hands — and both",
        "happen inside Notion, never in a terminal.",
        "",
        f"LUCAS: 1. mint it — {INTEGRATIONS} → New integration → name it 'WOS',",
        "          capabilities Read content + Update content + Insert content. Paste the",
        "          Internal Integration Secret (it starts with 'ntn_') into the conversation.",
        "       2. connect it — open the page in Notion → ⋯ → Connections → add 'WOS'.",
        "          A parent connection covers everything under it, so the class root is",
        "          usually the only click.",
        "",
        *_store_step(alias),
    ])


def revoked_text(alias: str) -> str:
    """401: the stored secret is not the live one. Nothing refreshes; only replacement works."""
    return "\n".join([
        f"NOTION REJECTED THE TOKEN (401) — workspace '{alias}'.",
        "The stored secret is wrong or was revoked. An integration token has no refresh step —",
        "a new secret is the only recovery.",
        "",
        f"LUCAS: {INTEGRATIONS} → the WOS integration → Secrets → show or regenerate it, and",
        "paste the new value into the conversation.",
        "",
        *_store_step(alias),
    ])


def not_shared_text(alias: str, target: str) -> str:
    """404/403: almost always an unshared page, so say that before doubting the id."""
    return "\n".join([
        f"NOTION CANNOT SEE IT — '{target}' (workspace '{alias}').",
        "Notion answers the same code for 'not connected to this integration' and for 'no such",
        "id', and the first is far more common: content is invisible until shared, not forbidden.",
        "",
        "LUCAS: open it in Notion → ⋯ → Connections → add 'WOS'. A parent connection covers its",
        "children, so sharing the class root fixes every page under it at once.",
        "",
        f"AGENT: once he has, run {CLI} list --account {alias} yourself — it prints everything",
        "the token reaches. If the page is still absent from that list, the id is the problem.",
    ])
