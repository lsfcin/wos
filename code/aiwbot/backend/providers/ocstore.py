# ocstore.py — read-only reads of opencode's sqlite store: session rows + last assistant answer.
from __future__ import annotations
import json
import pathlib
import sqlite3

_DB = ".local/share/opencode/opencode.db"
# The session row already carries mode + model, so those two need no join (SPECS AD-11).
# Its `tokens_*` columns deliberately are NOT read: they accumulate over the whole session
# (a real one here summed to 175% of its window), so they measure spend, not occupancy.
_SESSIONS_SQL = ("SELECT id, title, time_updated, agent, model "
                 "FROM session WHERE directory = ? AND parent_id IS NULL")
_MESSAGES_SQL = ("SELECT id, data FROM message WHERE session_id = ? "
                 "ORDER BY time_created DESC LIMIT ?")
# Which models Lucas actually reaches for. The curated shortlist guessed at cheap-and-good and
# guessed wrong — it offered models used once while the real top three had 91, 42 and 15 sessions.
_RECENT_SQL = ("SELECT model, time_updated FROM session "
               "WHERE model IS NOT NULL AND time_updated > ?")
_PARTS_SQL = "SELECT data FROM part WHERE message_id = ? ORDER BY time_created"
# How far back to look for the last assistant turn. A handful of trailing user/tool messages
# is normal; anything deeper means the session ended without an answer.
_MESSAGE_TAIL = 20


def _db_path() -> pathlib.Path:
    return pathlib.Path.home() / _DB


def _connect() -> sqlite3.Connection | None:
    """Read-only handle, or None when opencode was never used on this machine."""
    db = _db_path()
    con = None
    if db.exists():
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    return con


def _query(sql: str, params: tuple) -> list[tuple]:
    con = _connect()
    rows: list[tuple] = []
    if con is not None:
        cursor = con.execute(sql, params)
        rows = cursor.fetchall()
        con.close()
    return rows


def session_rows(cwd: str) -> list[tuple]:
    """Top-level sessions for cwd: (id, title, time_updated_ms, agent, model_json)."""
    return _query(_SESSIONS_SQL, (cwd,))


def recent_models(since_ms: float) -> list[tuple[str, int, float]]:
    """(model id, sessions started, last used) since a cutoff, most-used first and ties broken
    by recency. Session rows carry the model, so this is one query over an index the store keeps
    anyway — no message join."""
    rows = _query(_RECENT_SQL, (since_ms,))
    counts: dict[str, int] = {}
    last: dict[str, float] = {}
    for raw, updated in rows:
        model = model_of(raw)
        if not model:
            continue
        counts[model] = counts.get(model, 0) + 1
        previous = last.get(model, 0)
        last[model] = max(previous, updated)
    ranked = [(model, count, last[model]) for model, count in counts.items()]
    ranked.sort(key=lambda item: (item[1], item[2]), reverse=True)
    return ranked


def _catalogue_id(provider: str | None, model: str | None) -> str | None:
    """`providerID` + `id` joined into the one id every other part of the bot uses — the picker,
    the catalogue, the button labels. The store keeps the two halves apart in both places it
    records a model, so the join is written once here."""
    result = None
    if provider and model:
        result = f"{provider}/{model}"
    return result


def model_of(model_json: str | None) -> str | None:
    """session.model is JSON `{"id","providerID","variant"}`; the catalogue id that both
    `opencode models` and models.json use is `providerID/id`."""
    result = None
    if model_json:
        obj = json.loads(model_json)
        model = obj.get("id")
        provider = obj.get("providerID")
        result = _catalogue_id(provider, model)
    return result


def _text_parts(message_id: str) -> str:
    rows = _query(_PARTS_SQL, (message_id,))
    chunks: list[str] = []
    for (raw,) in rows:
        part = json.loads(raw)
        kind = part.get("type")
        if kind == "text":
            text = part.get("text") or ""
            chunks.append(text)
    return "\n".join(chunks)


def context_used(data: dict) -> int | None:
    """Occupancy after one assistant message: fresh input + both cache halves — the same
    formula claude's result object gets (AD-9). Per MESSAGE, never summed over the session."""
    tokens = data.get("tokens") or {}
    cache = tokens.get("cache") or {}
    counts = [tokens.get("input"), cache.get("read"), cache.get("write")]
    total = sum(count or 0 for count in counts)
    result = total or None
    return result


def _last_assistant(session_id: str) -> tuple[str, dict] | None:
    """Filtering by role is not optional: `part` rows of type=text also carry the USER's
    message and injected system-reminders, so a naive last-text-part preview would quote
    Lucas back at himself."""
    rows = _query(_MESSAGES_SQL, (session_id, _MESSAGE_TAIL))
    found = None
    for mid, raw in rows:
        data = json.loads(raw)
        role = data.get("role")
        if role == "assistant":
            found = (mid, data)
            break
    return found


def last_model(session_id: str) -> str | None:
    """Which model actually answered last in this session. The JSONL stream names a model NOWHERE
    — not on the text lines, not on step_finish — so a bot answer's footer had no model to print
    at all (Lucas, live 2026-07-29). The assistant message in the store does carry it."""
    message = _last_assistant(session_id)
    result = None
    if message is not None:
        _mid, data = message
        provider = data.get("providerID")
        model = data.get("modelID")
        result = _catalogue_id(provider, model)
    return result


def last_turn(session_id: str) -> tuple[str, int | None]:
    """(answer text, context occupancy) of the session's last assistant turn. One pair of
    queries, so the picker asks for it per PAGE, not per listed session."""
    message = _last_assistant(session_id)
    text = ""
    used = None
    if message is not None:
        mid, data = message
        text = _text_parts(mid)
        used = context_used(data)
    return text, used
