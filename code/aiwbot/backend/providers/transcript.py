# transcript.py — read a claude .jsonl transcript from the tail for title/preview/context %.
from __future__ import annotations
import pathlib
from ..base import try_json

_AI_TITLE = '"type":"ai-title"'
_ASSISTANT = '"type":"assistant"'


def tail_lines(path: pathlib.Path, kb: int = 64) -> list[str]:
    """Last ~kb KB of the transcript as decoded lines. Latest events sit near EOF, so a
    bounded tail is enough to find the current title / last response cheaply."""
    size = path.stat().st_size
    start = max(0, size - kb * 1024)
    with path.open("rb") as handle:
        handle.seek(start)
        raw = handle.read()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return lines


def latest_ai_title(lines: list[str]) -> str:
    """Latest `ai-title` event = Claude Code's current picker title. Scan from the end."""
    title = ""
    for line in reversed(lines):
        if _AI_TITLE not in line:
            continue
        obj = try_json(line.strip())
        if obj is not None:
            title = obj.get("aiTitle") or ""
        break
    return title


def _last_assistant_message(lines: list[str]) -> dict | None:
    """The `message` object of the last assistant event (role/model/content/usage)."""
    message: dict | None = None
    for line in reversed(lines):
        if _ASSISTANT not in line:
            continue
        obj = try_json(line.strip())
        if obj is not None:
            message = obj.get("message")
        break
    return message


def _text_of(content: object) -> str:
    """Last text block of an assistant `message.content` list."""
    text = ""
    if isinstance(content, list):
        for block in reversed(content):
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text") or ""
                break
    return text


def last_response_text(lines: list[str]) -> str:
    """Text of the session's last assistant response — source for the /resume preview."""
    message = _last_assistant_message(lines)
    text = ""
    if isinstance(message, dict):
        content = message.get("content")
        text = _text_of(content)
    return text


# Transcript usage is snake_case (the live result object uses camelCase — see claude._context_of).
_CONTEXT_FIELDS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def last_context_used(lines: list[str]) -> int | None:
    """Context occupancy of the last assistant turn, from its `usage` breakdown. The window
    itself is NOT in the transcript — the frontend pairs this with a window learned live."""
    message = _last_assistant_message(lines)
    used = None
    if isinstance(message, dict):
        usage = message.get("usage") or {}
        if usage:
            counts = [usage.get(f) or 0 for f in _CONTEXT_FIELDS]
            used = sum(counts)
    return used


def last_model(lines: list[str]) -> str | None:
    """Model of the last assistant response (e.g. claude-sonnet-5), if recorded."""
    message = _last_assistant_message(lines)
    model: str | None = None
    if isinstance(message, dict):
        model = message.get("model")
    return model
