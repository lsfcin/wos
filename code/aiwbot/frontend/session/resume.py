# resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .. import config, phrases, reply
from ..text import format
from . import msgmap, registry, sessions
from ..select import panelmenu

RESUME_COUNT = 3
TITLE_WORDS = 5
QUERY_MAX = 40  # callback_data caps at 64 bytes; the page arrows carry the active filter
# A monospace run of non-breaking spaces pins a minimum bubble width, so the message stops
# resizing as pages of different content go by. Monospace makes the width predictable; NBSP
# is what survives client-side trimming.
# To actually pin the width the ruler has to out-measure the longest content line, which is
# format.PREVIEW_CHARS (64) of proportional text — monospace runs wider per character, so
# fewer of them are needed. 44 is an eyeball estimate: too low and wide pages still stretch
# the bubble, too high and every page is padded to the full screen. Tune it live.
# Set to 0 to remove the ruler entirely.
RULER_WIDTH = 44
_NBSP = " "
_NOOP = "noop:"


def _meta(item: dict) -> str:
    """L3: provider · modelo · modo · X%contexto · quando — bits omitted when absent."""
    used = item.get("context_used")
    window = item.get("context_window")
    bits = format.meta_bits(item["backend"], item.get("model"), item.get("mode"), used, window)
    when = format.relative_time(item["updated_at"])
    bits.append(when)
    return " · ".join(bits)


def _entry_line(i: int, item: dict) -> str:
    """3 lines: `N. TÍTULO` / `<6 words> … <6 words>` of the last response / meta line."""
    title = format.title_words(item["title"], TITLE_WORDS)
    lines = [f"{i}. {title}"]
    preview = item.get("preview")
    if preview:
        rendered = format.response_preview(preview)
        lines.append(rendered)
    meta = _meta(item)
    lines.append(meta)
    return "\n".join(lines)


def _list_text(items: list[dict], start: int = 1) -> str:
    blocks = []
    for i, item in enumerate(items, start=start):
        block = _entry_line(i, item)
        blocks.append(block)
    return "\n\n".join(blocks)


def _arrow(glyph: str, target: int, query: str, live: bool) -> InlineKeyboardButton:
    """Arrows keep their slot at both ends of the range so the row never changes shape —
    at an end the glyph stays put and the tap simply does nothing."""
    data = _NOOP
    if live:
        data = f"page:{target}:{query}"
    return InlineKeyboardButton(glyph, callback_data=data)


def _keyboard(items: list[dict], offset: int = 0, query: str = "", total: int = 0) -> InlineKeyboardMarkup:
    """Always five slots: ‹ then the page's absolute numerals then ›. Numbering runs 1 2 3,
    4 5 6, … so a numeral always names the same session as the line above it (AD-5)."""
    back = offset - RESUME_COUNT
    if back < 0:
        back = 0
    row = [_arrow("«", back, query, offset > 0)]
    for i, item in enumerate(items, start=offset + 1):
        data = f"resume:{item['session_id']}"
        button = InlineKeyboardButton(str(i), callback_data=data)
        row.append(button)
    shown = offset + len(items)
    row.append(_arrow("»", shown, query, shown < total))
    return InlineKeyboardMarkup([row])


def _ruler() -> str:
    """Injected after escaping — `_page` escapes the whole picker text, which would turn
    these tags into literal <code> on screen."""
    result = ""
    if RULER_WIDTH:
        pad = _NBSP * RULER_WIDTH
        result = f"\n<code>{pad}</code>"
    return result


def _header(total: int, shown: int, query: str) -> str:
    base = f"Sessões recentes — {shown} de {total}"
    if query:
        base += f' · filtro "{query}"'
    return base


def _page(query: str, cwd: str, offset: int, count: int) -> tuple[str, InlineKeyboardMarkup] | None:
    """One page of the picker: message text + its ‹ N N N › keyboard. None when nothing matches."""
    items = sessions.recent(count, query, cwd, offset)
    result = None
    if items:
        total = sessions.count(query, cwd)
        header = _header(total, offset + len(items), query)
        listing = _list_text(items, offset + 1)
        text = f"{header}\n\n{listing}"
        keyboard = _keyboard(items, offset, query, total)
        escaped = format.plain(text)
        ruler = _ruler()
        result = (escaped + ruler, keyboard)
    return result


async def cmd_resume(msg, arg: str, cwd: str) -> None:
    """The page size is fixed. It used to be settable as `/resume N`, but `_turn_page` always
    paged by RESUME_COUNT, so page 1 showed 1-5 while page 2 showed 4-6 — the same numeral
    naming two different sessions, which is the one thing AD-5 exists to prevent. A bare
    number is now just a filter term, so `/resume 2026` searches titles."""
    query = arg.strip()
    page = _page(query[:QUERY_MAX], cwd, 0, RESUME_COUNT)
    if page is None:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.RESUME_EMPTY_PHRASES)))
        return
    text, keyboard = page
    await reply.safe_reply(msg, text, reply_markup=keyboard)


async def _turn_page(query, data: str) -> None:
    """‹ / › tap: re-render the same message at the new offset (filter rides in callback_data)."""
    parts = data.split(":", 2)
    offset = int(parts[1])
    term = parts[2]
    page = _page(term, config.WORKSPACE_DIR, offset, RESUME_COUNT)
    if page is None:
        return
    text, keyboard = page
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def _anchor(query, sid: str) -> None:
    title = registry.title_for(sid)
    backend = registry.backend_for(sid)
    last = sessions.last_response(sid, config.WORKSPACE_DIR)
    body = last or None
    phrase = phrases.pick(phrases.RESUME_ANCHOR_PHRASES)
    block = format.session_block(phrase, sid, title, body=body, backend=backend)
    # The anchor is a repliable message like any answer, so it carries the same mode toggle:
    # without it you re-anchor a session unable to see the mode you're about to run in.
    markup = panelmenu.root_markup(sid)
    # Delivered exactly like an answer — split on paragraph boundaries, every bubble anchored.
    # It used to be one `safe_reply` over a body hard-clipped at 3000 chars, which is where the
    # `[…]` Lucas hit came from: not Telegram's 4096 limit, ours, and mid-word (F5b).
    sent = await reply.deliver(None, query.message, block, reply_markup=markup)
    for message in sent:
        msgmap.remember_reply(message.message_id, sid)


async def handle_callback(update, context) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    data = query.data or ""
    await query.answer()
    if data.startswith("resume:"):
        sid = data.split(":", 1)[1]
        await _anchor(query, sid)
    elif data.startswith("page:"):
        await _turn_page(query, data)
    # `noop:` is an arrow parked at the end of the range — answering the callback above already
    # dismissed the spinner, so there is deliberately nothing left to do here.
