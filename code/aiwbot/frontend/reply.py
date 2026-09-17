# reply.py — Telegram send primitives: safe reply, chunking, edit-in-place delivery.
from __future__ import annotations
from telegram.constants import ChatAction
from telegram.error import TelegramError
from .stream import answer
from .text import split_html, strip_tags

TELEGRAM_MSG_LIMIT = 4096
# Lucas, 2026-07-27: a long answer should arrive as several bubbles even when one would fit —
# "partir a resposta em várias mensagens pra parecer mais como uma conversação". This is the
# size a chunk wants to reach before it looks for a paragraph break to end on; the hard limit
# above still governs. Eyeball value, tune it by reading real answers in the chat.
SOFT_CHARS = 900
# Telegram's wording when it rejects our markup rather than the request itself. Retrying the
# same HTML after one of these is pointless — the content is what it objects to.
_PARSE_MARKERS = ("parse entities", "start tag", "end tag", "entity")


def _is_parse_error(e: TelegramError) -> bool:
    text = str(e).lower()
    result = False
    for marker in _PARSE_MARKERS:
        if marker in text:
            result = True
            break
    return result


async def _send(msg, text: str, markup, parse_mode: str | None) -> "telegram.Message | None":
    return await msg.reply_text(text, parse_mode=parse_mode, do_quote=True, reply_markup=markup)


async def _send_plain(msg, html_text: str, reply_markup) -> "telegram.Message | None":
    """Telegram refused our markup: send the same content with the tags stripped. A message
    that lost its formatting still beats a message that silently never arrives."""
    bare = strip_tags(html_text)
    result = None
    try:
        result = await _send(msg, bare, reply_markup, None)
    except TelegramError as e:
        print(f"plain-text fallback failed too: {e}")
    return result


async def safe_reply(msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    result = None
    for attempt in range(2):
        try:
            result = await _send(msg, html_text, reply_markup, "HTML")
            break
        except TelegramError as e:
            if _is_parse_error(e):
                result = await _send_plain(msg, html_text, reply_markup)
                break
            if attempt == 1:
                print(f"reply_text failed after retry: {e}")
    return result


async def send_typing(message) -> None:
    """Light Telegram's native "typing…" indicator in the chat header. Best-effort: it is a
    decoration on top of an answer that is arriving anyway, so a failure is dropped rather than
    allowed to interrupt the turn. It expires after ~5s and must be re-sent to stay lit."""
    try:
        await message.chat.send_action(ChatAction.TYPING)
    except TelegramError as e:
        print(f"send_typing failed: {e}")


async def edit_text(message, html_text: str, reply_markup=None) -> bool:
    """Repaint one live message. Returns whether Telegram accepted it.

    "Message is not modified" is not an error here — it means the throttle let through a paint
    whose content had not actually changed — so it is reported as success and never retried,
    while a real failure (rate limit, network) is left for the caller's backoff to widen."""
    ok = False
    try:
        await message.edit_text(html_text, parse_mode="HTML", reply_markup=reply_markup)
        ok = True
    except TelegramError as e:
        if "not modified" in str(e).lower():
            ok = True
        else:
            print(f"stream edit failed: {e}")
    return ok


async def _edit_or_send(working_msg, msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    """Morph the ⏳ working message into the final text (feels like a substitution);
    fall back to a fresh reply if the edit is rejected (too old, identical, unparseable)."""
    sent = None
    if working_msg is not None:
        try:
            sent = await working_msg.edit_text(html_text, parse_mode="HTML", reply_markup=reply_markup)
        except TelegramError as e:
            print(f"edit failed, sending instead: {e}")
    if sent is None:
        sent = await safe_reply(msg, html_text, reply_markup=reply_markup)
    return sent


async def send_voice(msg, ogg_bytes: bytes) -> "telegram.Message | None":
    """Best-effort voice reply (C5): text has already been delivered, so a rejected voice
    send degrades to None — mirrors safe_reply's tolerance for Telegram-side errors."""
    result = None
    try:
        result = await msg.reply_voice(ogg_bytes)
    except TelegramError as e:
        print(f"send_voice failed: {e}")
    return result


async def drop(message) -> bool:
    """Remove one of the bot's own messages. Best-effort: a status bubble that cannot be deleted
    is a cosmetic problem, never a reason to fail a turn."""
    ok = False
    try:
        await message.delete()
        ok = True
    except TelegramError as e:
        print(f"delete failed: {e}")
    return ok


async def deliver(working_msg, msg, html_text: str, reply_markup=None, lead: str = "") -> list:
    """Returns EVERY message sent, not just the last. A long answer arrives as several bubbles
    and Lucas replies to whichever one he happens to be reading — so the caller has to be able
    to anchor all of them to the session. Anchoring only the tail is what made a reply to an
    earlier bubble fall through to INBOX capture instead of continuing the turn (F5a)."""
    chunks = split_html(html_text, answer.room(TELEGRAM_MSG_LIMIT, lead), SOFT_CHARS)
    chunks = answer.decorate(chunks, lead, total=len(chunks))
    first = chunks[0]
    single = len(chunks) == 1
    markup = reply_markup if single else None
    sent = []
    opener = await _edit_or_send(working_msg, msg, first, markup)
    if opener is not None:
        sent.append(opener)
    for i, chunk in enumerate(chunks[1:]):
        is_last = i == len(chunks) - 2
        tail_markup = reply_markup if is_last else None
        nxt = await safe_reply(msg, chunk, reply_markup=tail_markup)
        if nxt is not None:
            sent.append(nxt)
    return sent
