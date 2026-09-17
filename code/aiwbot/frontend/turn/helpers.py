# helpers.py — turn plumbing: friendly errors, /new arg parsing, sticky options, persistence.
# Extracted out of bot.py (size gate) — pure helpers with no test-visible monkeypatch boundary.
from __future__ import annotations
from backend import TurnOptions, get_backend
from ..interview import ask, askserver
from . import directives
from ..text import format
from ..select import panel
from .. import phrases
from ..session import registry

_BUSY_MARKERS = ("no conversation found", "currently running as a background agent")
# Failures that are about the moment rather than about the request: the provider was overloaded,
# rate-limited, or the connection timed out. Worth retrying exactly because Lucas is usually not
# watching — a 529 that killed his turn cost him the whole task, not a few seconds (2026-07-29).
# The list is per-provider VOCABULARY, not per-provider logic: opencode says the same thing in
# words claude never uses ("ResourceExhausted: Worker local total request limit reached (48/48)",
# captured live for b2), and until those were here the retry above was claude-only in practice.
_TRANSIENT_MARKERS = ("529", "overloaded", "rate limit", "rate_limit", "timed out", "timeout",
                      "502", "503", "504", "connection reset", "temporarily",
                      "resourceexhausted", "request limit reached")


def friendly_error(e: Exception) -> str:
    text = str(e).lower()
    busy = any(marker in text for marker in _BUSY_MARKERS)
    if busy:
        result = format.plain(phrases.pick(phrases.SESSION_LIVE_ELSEWHERE_PHRASES))
    else:
        result = format.plain(phrases.pick(phrases.ERROR_PHRASES, e=e))
    return result


def transient(e: Exception) -> bool:
    """Is this failure worth trying again as-is? Only server-side/transport ones — a bad prompt or
    a missing session would fail identically on every attempt, so retrying it just spends time."""
    text = str(e).lower()
    hit = False
    for marker in _TRANSIENT_MARKERS:
        if marker in text:
            hit = True
            break
    return hit


def parse_new_arg(arg: str) -> tuple[str | None, str]:
    """`--backend X` still works and now simply writes the NEW scope's harness, so typing it
    and tapping it are the same act on the same state."""
    backend_name = None
    prompt = arg
    if arg.startswith("--backend "):
        rest = arg[len("--backend "):]
        parts = rest.split(maxsplit=1)
        backend_name = parts[0]
        prompt = parts[1] if len(parts) > 1 else ""
    return backend_name, prompt


def apply_directives(bot_prompt: str) -> str:
    """A `bot, …` message can name its own harness/model inline ("bot, opencode glm resume o
    pdf"); write those onto the NEW scope so the turn inherits them, and return the prompt with
    the directive words removed. Reuses `panel.apply` so an inline harness change clears a stale
    model exactly as a tapped one does — the invalidation rule stays in one place."""
    harness, model, rest = directives.resolve(bot_prompt)
    if harness:
        panel.apply(registry.NEW, "h", harness)
    if model:
        panel.apply(registry.NEW, "m", model)
    return rest


def turn_options(scope: str, title: str | None) -> TurnOptions:
    """The turn's knobs, read off the scope that owns them: a live session, or NEW for the
    last-used defaults a fresh session inherits."""
    mode_name = registry.mode_for(scope)
    model = registry.setting_for(scope, "model")
    effort = registry.setting_for(scope, "effort")
    streaming = registry.streams(scope)
    return TurnOptions(mode=mode_name, title=title, model=model, effort=effort, stream=streaming)


def enable_ask(scope: str, backend_name: str, options: TurnOptions) -> str | None:
    """Give this turn a way to ask Lucas something, when the scope allows it, the backend can use
    one, and the broker is actually listening. Returns the turn's token (the caller owns
    registering and releasing it), or None — in which case the CLI is invoked exactly as before
    and the agent simply has no ask tool, which is how every off switch here degrades: to Stage 3
    behaviour, never to a broken turn."""
    token = None
    backend = get_backend(backend_name)
    listening = askserver.port() if registry.asks(scope) else 0
    if listening and backend.supports_ask(options):
        token = ask.new_token()
        options.ask_url = askserver.url(token, listening)
    return token


def persist_turn(session_id: str, backend_name: str, title: str | None, result, options: TurnOptions) -> None:
    """Carry the knobs onto the session the turn ran on, and onto the defaults, so the next
    /new starts where the last interaction left off."""
    preview = format.response_preview(result.text)
    registry.remember(session_id, backend_name, title, preview)
    registry.set_mode(session_id, options.mode)
    registry.set_setting(session_id, "model", options.model)
    registry.set_setting(session_id, "effort", options.effort)
    registry.remember_defaults(backend_name, options.mode, options.model, options.effort)
    registry.remember_context_window(result.model, result.context_window)
