# registry.py — bot-owned per-session state in config.json: knobs, titles, message maps.
# Side-state only: the provider stores stay the source of truth for what sessions exist (AD-6).
from __future__ import annotations
import time
from .. import config
from . import msgmap

DEFAULT_BACKEND = "claude"
DEFAULT_MODE = "build"


def _entries() -> dict:
    return config.load_config().get("sessions", {})


def remember(session_id: str, backend: str, title: str | None = None, preview: str | None = None) -> None:
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    now = time.time()
    sessions[session_id] = {"backend": backend, "title": title, "preview": preview, "updated_at": now}
    config.save_config(sessions=sessions)


def adopt(session_id: str, backend: str, title: str | None, updated_at: float) -> None:
    """Cache a store-listed session's backend/title into the registry (preserving any existing
    mode/preview) so anchor + reply-to-continue resolve it — even VSCode sessions we didn't create."""
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    entry = sessions.get(session_id, {})
    entry["backend"] = backend
    entry["title"] = title
    entry["updated_at"] = updated_at
    entry.setdefault("preview", None)
    sessions[session_id] = entry
    config.save_config(sessions=sessions)


# The panel edits knobs for two things: a live session, or the session /new is about to create.
# Both are addressed as a "scope" so the panel code stays scope-agnostic — NEW routes to the
# last-used defaults, any other value is a session id. The sentinel lives in msgmap because that
# is what a /new config bubble is tagged with.
NEW = msgmap.NEW


def defaults() -> dict:
    """Knobs the last turn ran with. A new session inherits them, so the harness/model you
    chose yesterday is still what /new starts on today."""
    return config.load_config().get("defaults", {})


def _set_default(key: str, value: str | None) -> None:
    entry = defaults()
    entry[key] = value
    config.save_config(defaults=entry)


def _set_session(session_id: str, key: str, value: str | None) -> None:
    """Unknown sessions are ignored on purpose: every message carrying a panel was remembered
    or adopted first, so a write against an unknown id means a stale keyboard, not a new
    session."""
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    entry = sessions.get(session_id)
    if entry is not None:
        entry[key] = value
        config.save_config(sessions=sessions)


def _scope_entry(scope: str) -> dict:
    entry = defaults() if scope == NEW else _entries().get(scope, {})
    return entry


def setting_for(scope: str, key: str, default: str | None = None) -> str | None:
    """One sticky knob (mode/model/effort) for a scope. Unset reads as the default, which is
    how "let the harness decide" stays distinct from a value that was actually picked."""
    entry = _scope_entry(scope)
    return entry.get(key) or default


def set_setting(scope: str, key: str, value: str | None) -> None:
    if scope == NEW:
        _set_default(key, value)
    else:
        _set_session(scope, key, value)


def harness_for(scope: str) -> str:
    """The harness a scope runs on. For a session that is fixed at creation; for NEW it is the
    one knob /new can still change."""
    if scope == NEW:
        chosen = setting_for(NEW, "backend", DEFAULT_BACKEND)
    else:
        chosen = backend_for(scope) or DEFAULT_BACKEND
    return chosen or DEFAULT_BACKEND


def remember_defaults(backend: str, mode: str, model: str | None, effort: str | None) -> None:
    """Called after every turn so /new inherits the last interaction's knobs."""
    entry = defaults()
    entry["backend"] = backend
    entry["mode"] = mode
    entry["model"] = model
    entry["effort"] = effort
    config.save_config(defaults=entry)


def backend_for(session_id: str) -> str | None:
    """The harness that owns this lineage — the only one that can resume this id, and the
    reason harness is NOT a per-session knob: no CLI can import the other's transcript
    (opencode has `export`/`import`, claude has no counterpart), so a running session can
    never change harness. It is chosen once, at /new (SPECS AD-11)."""
    entry = _entries().get(session_id, {})
    return entry.get("backend")


# Streaming changes how the CLI is invoked, so its rollback has to be reachable from Lucas's
# phone: one line in config.json plus a daemon restart, never a code change (F4). Flipped to True
# once the mid-stream sealing checkpoint passes.
STREAM_DEFAULT = False


def streams(scope: str) -> bool:
    """Whether this scope's turns stream. Stored as a string like every other knob, so the
    existing per-scope machinery (and a future panel dimension) needs no special case."""
    return _flag(scope, "stream", STREAM_DEFAULT)


# Same rollback shape as streaming, for the same reason: `"ask": "false"` plus a restart takes
# the tool away from the agent without touching code (F4 Stage 4).
ASK_DEFAULT = True


def asks(scope: str) -> bool:
    """Whether this scope's turns may stop and ask Lucas something mid-turn."""
    return _flag(scope, "ask", ASK_DEFAULT)


def _flag(scope: str, name: str, default: bool) -> bool:
    raw = setting_for(scope, name)
    result = default
    if raw is not None:
        result = str(raw).lower() in ("1", "true", "yes", "on")
    return result


def mode_for(scope: str, default: str = DEFAULT_MODE) -> str:
    """Build, always (Lucas, 2026-07-28 — option A of the AD-27 decision).

    The CLI refuses every MCP tool in plan mode, which would take `ask_user` away exactly where
    interviewing pays off, so the bot stopped offering plan at all. This coerces rather than
    reads: a session whose stored mode says `plan` — set before this decision, or continued from
    a desktop session that was planning — comes back as build instead of resurrecting a mode the
    bot cannot support. The argument is kept so callers read the same, and so restoring plan is
    one line if a future CLI lifts the block."""
    return DEFAULT_MODE


def set_mode(scope: str, mode: str) -> None:
    set_setting(scope, "mode", mode)


def title_for(session_id: str) -> str | None:
    entry = _entries().get(session_id, {})
    return entry.get("title")


def remember_context_window(model: str | None, window: int | None) -> None:
    """Learn a model's context window from a live turn. Claude transcripts don't record it, so
    the /resume list reuses what we've observed instead of hardcoding per-model constants."""
    if model and window:
        cfg = config.load_config()
        windows = cfg.get("context_windows", {})
        windows[model] = window
        config.save_config(context_windows=windows)


def context_window_for(model: str | None) -> int | None:
    """Observed context window for a model, or None if we've never seen a live turn on it."""
    windows = config.load_config().get("context_windows", {})
    return windows.get(model or "")
