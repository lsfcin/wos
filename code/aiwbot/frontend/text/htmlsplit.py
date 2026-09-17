# htmlsplit.py — split Telegram HTML into sendable chunks without ever breaking a tag.
from __future__ import annotations
import html
import re

_TAG_RE = re.compile(r"<(/?)([a-z]+)(?:\s[^>]*)?>")
# Slack for the reopen prefix a hard slice can't predict; a few bytes are cheaper than a
# chunk that overshoots the limit and gets rejected.
_MARGIN = 16
_MIN_BUDGET = 64


def _apply_tags(stack: list[tuple[str, str]], line: str) -> None:
    """Advance the open-tag stack across one line. A closer with no opener is ignored rather
    than raising: agent text isn't guaranteed well-formed, and dropping the message is worse."""
    for match in _TAG_RE.finditer(line):
        closing = match.group(1)
        name = match.group(2)
        if not closing:
            full = match.group(0)
            stack.append((name, full))
            continue
        found = -1
        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == name:
                found = i
                break
        if found >= 0:
            stack.pop(found)


def _reopen(stack: list[tuple[str, str]]) -> str:
    """Opening tags verbatim — an <a href=…> has to come back with its href intact."""
    parts = []
    for _, full in stack:
        parts.append(full)
    return "".join(parts)


def _close(stack: list[tuple[str, str]]) -> str:
    parts = []
    for name, _ in reversed(stack):
        parts.append(f"</{name}>")
    return "".join(parts)


def _hard_slice(line: str, budget: int) -> tuple[str, str]:
    """Last resort for one line longer than a whole chunk: cut where it cannot land inside
    a tag, so both halves stay parseable."""
    cut = budget
    opened = line.rfind("<", 0, cut)
    closed = line.rfind(">", 0, cut)
    if opened > closed:
        cut = opened
    if cut <= 0:
        cut = budget
    head = line[:cut]
    tail = line[cut:]
    return head, tail


def _sealed(prefix: str, body: list[str], stack: list[tuple[str, str]]) -> str:
    """One finished chunk: reopened where the last one left off, closed where this one ends."""
    joined = "\n".join(body)
    suffix = _close(stack)
    return prefix + joined + suffix


def _has_text(lines: list[str]) -> bool:
    """Any actual content, ignoring blank lines and the tags carried across a boundary. Telegram
    rejects an empty message, so a run of blank lines must never seal a chunk of its own."""
    joined = "".join(lines)
    stripped = _TAG_RE.sub("", joined)
    return bool(stripped.strip())


def _wants_break(grown: str, line: str, soft: int | None, body: list[str]) -> bool:
    """Has this chunk grown past its comfortable size AND reached a paragraph break? Only a
    blank line qualifies, so a chunk never ends mid-thought — the split is meant to read like
    someone sending several messages, not like a message cut in half (F5b)."""
    result = False
    if soft is not None and len(grown) >= soft and not line.strip():
        result = _has_text(body)
    return result


def split_html(text: str, limit: int, soft: int | None = None) -> list[str]:
    """Chunk formatted HTML on line boundaries, carrying open tags across the boundary: whatever
    is still open is closed at the end of a chunk and reopened at the start of the next.

    `limit` is Telegram's hard cap and is never exceeded. `soft`, when given, is the size past
    which a chunk ends at the next paragraph break — that is what turns one wall of text into a
    conversation instead of a single bubble."""
    queue = text.split("\n")
    chunks: list[str] = []
    stack: list[tuple[str, str]] = []
    body: list[str] = []
    prefix = ""
    while queue:
        line = queue.pop(0)
        after = list(stack)
        _apply_tags(after, line)
        candidate = body + [line]
        grown = _sealed(prefix, candidate, after)
        if len(grown) <= limit:
            body = candidate
            stack = after
            if _wants_break(grown, line, soft, body):
                sealed = _sealed(prefix, body, stack)
                chunks.append(sealed)
                prefix = _reopen(stack)
                body = []
            continue
        if body:
            sealed = _sealed(prefix, body, stack)
            chunks.append(sealed)
            prefix = _reopen(stack)
            body = []
            queue.insert(0, line)
            continue
        head, tail = _oversized(line, prefix, stack, limit)
        _apply_tags(stack, head)
        sealed = _sealed(prefix, [head], stack)
        chunks.append(sealed)
        prefix = _reopen(stack)
        queue.insert(0, tail)
    if body or not chunks:
        sealed = _sealed(prefix, body, stack)
        chunks.append(sealed)
    return chunks


def _oversized(line: str, prefix: str, stack: list[tuple[str, str]], limit: int) -> tuple[str, str]:
    """Budget left for a line that doesn't fit even alone in a fresh chunk."""
    suffix = _close(stack)
    budget = limit - len(prefix) - len(suffix) - _MARGIN
    if budget < _MIN_BUDGET:
        budget = _MIN_BUDGET
    return _hard_slice(line, budget)


def strip_tags(text: str) -> str:
    """Plain-text fallback body, for when Telegram refuses to parse the entities at all."""
    bare = _TAG_RE.sub("", text)
    return html.unescape(bare)
