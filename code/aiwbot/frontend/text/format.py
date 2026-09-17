# format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O.
from __future__ import annotations
import html
import time
from .markdown import format_body

SESSION_ID_LABEL_LEN = 3


def relative_time(ts: float, now: float | None = None) -> str:
    """Human relative age like Claude Code's resume picker: agora / 5m atrás / 2h atrás / 3d atrás."""
    ref = now
    if ref is None:
        ref = time.time()
    delta = ref - ts
    result = "agora"
    if delta >= 86400:
        days = int(delta // 86400)
        result = f"{days}d atrás"
    elif delta >= 3600:
        hours = int(delta // 3600)
        result = f"{hours}h atrás"
    elif delta >= 60:
        mins = int(delta // 60)
        result = f"{mins}m atrás"
    return result


def plain(text: str) -> str:
    return html.escape(text)


TITLE_CHARS = 32
PREVIEW_CHARS = 64


def clip_chars(text: str, limit: int) -> str:
    """Hard character cap with an ellipsis. Word budgets alone let a line run 15 to 60 chars,
    which is what made the /resume bubble resize on every page turn — width is a character
    quantity, so it has to be budgeted as one."""
    result = text
    if len(text) > limit:
        head = text[:limit].rstrip()
        result = f"{head}…"
    return result


def title_words(name: str | None, n: int = 3, limit: int = TITLE_CHARS) -> str:
    """`limit` is separate from `n` because the two callers budget differently: the /resume
    picker needs a stable bubble WIDTH (hence the tight char cap), while an answer's footer is
    just a line of text and can afford more of the title."""
    result = "(SEM TÍTULO)"
    if name and name.strip():
        words = name.split()[:n]
        joined = " ".join(words)
        upper = joined.upper()
        result = clip_chars(upper, limit)
    return result


def title_from_prompt(prompt: str, n: int = 8) -> str:
    """Provider-agnostic session title: the first few words of the opening prompt."""
    words = prompt.split()
    return " ".join(words[:n])


def response_preview(text: str, n: int = 6) -> str:
    """First n … last n words of a response, for the /resume picker preview line, then capped
    in characters so a page of long-worded sessions doesn't widen the bubble."""
    words = text.split()
    result = " ".join(words)
    if len(words) > 2 * n:
        head = " ".join(words[:n])
        tail = " ".join(words[-n:])
        result = f"{head} … {tail}"
    return clip_chars(result, PREVIEW_CHARS)


# Provider as data: how each backend re-opens a session by id outside the bot.
_REATTACH = {"claude": "claude --resume {sid}", "opencode": "opencode -s {sid}"}


def reattach_cmd(sid: str, backend: str | None = None) -> str | None:
    """Copy-paste command to reopen a session in the terminal/VSCode. Bot `-p` sessions are
    resumable by id but never listed in Claude Code's own picker (SPECS AD-8), so the id is
    the only way out of the bot. None for a backend we don't know how to reattach."""
    key = backend or ""
    template = _REATTACH.get(key)
    result = None
    if template:
        result = template.format(sid=sid)
    return result


def session_block(phrase: str, sid: str | None, title: str | None, body: str | None = None,
                  extra: str | None = None, backend: str | None = None) -> str:
    lines = [html.escape(phrase)]
    if sid:
        header = f"[{sid[:SESSION_ID_LABEL_LEN].upper()}] {title_words(title)}"
        if extra:
            header += f" · {extra}"
        lines.append(html.escape(header))
        cmd = reattach_cmd(sid, backend)
        if cmd:
            escaped = html.escape(cmd)
            lines.append(f"<code>{escaped}</code>")
    if body:
        lines.append(format_body(body))
    return "\n".join(lines)


_MODEL_FAMILIES = ("sonnet", "opus", "haiku", "fable")


def short_model(model: str | None) -> str | None:
    """claude-sonnet-5 -> sonnet; nvidia/z-ai/glm-5.2 -> glm-5.2. Meta lines want the model to
    read as one word, and opencode ids are provider-qualified paths."""
    result = model
    if model:
        for family in _MODEL_FAMILIES:
            if family in model:
                result = family
                break
        else:
            result = model.rsplit("/", 1)[-1]
    return result


# A share of the window cannot exceed the window. Anything above this is a measurement bug, not
# a full context, so it is withheld rather than shown — b3 put "200%" in front of Lucas for days
# and a visibly missing number is a better bug report than a confidently wrong one.
_MAX_PCT = 100


def context_pct(used: int | None, window: int | None) -> str | None:
    """Context occupancy as `32%`. None unless the provider reported both numbers, and None
    when the pair is impossible — see `_MAX_PCT` and backend `occupancy()` (b3)."""
    result = None
    if used and window:
        ratio = 100 * used / window
        pct = round(ratio)
        if pct <= _MAX_PCT:
            result = f"{pct}%"
    return result


def meta_bits(provider: str | None, model: str | None, mode: str | None,
              used: int | None = None, window: int | None = None) -> list[str]:
    """Shared head of every meta line: provider · modelo · modo · X%. Callers append
    the tail that differs — `$custo` on answers, `quando` on the /resume list."""
    bits = []
    if provider:
        bits.append(provider)
    short = short_model(model)
    if short:
        bits.append(short)
    if mode:
        bits.append(mode)
    pct = context_pct(used, window)
    if pct:
        bits.append(pct)
    return bits


# The answer message's own shape (body + footer) lives in `answer.py` — this module stays pure
# text formatting that both an answer and the /resume list can share.
