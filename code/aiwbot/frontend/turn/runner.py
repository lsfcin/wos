# runner.py — run one turn and put its answer on screen: dispatch, deliver, anchor, speak.
#
# The impure sibling of helpers.py: that module DECIDES (pure, no I/O), this one DOES (awaits
# the backend and Telegram). Split out of bot.py for F4 — streaming changes "await the whole result,
# then deliver" into "paint as it arrives, then seal", and everything that changes is in here, so
# bot.py's PTB wiring and routing stay untouched by it.
from __future__ import annotations
import asyncio
from ..stream import answer, painter
from ..interview import ask
from . import dispatch, helpers
from ..session import msgmap, registry
from ..select import panelmenu
from .. import phrases, reply
from ..voice import speech, tts
from .. import config
from ..text import format

WORKSPACE_DIR = config.WORKSPACE_DIR
# The voice reply is synthesized from the answer, and a whole answer can be far longer than anyone
# wants read aloud, so the spoken copy is capped where the text one is not.
SPOKEN_CHARS = 2000
# How many times a transient failure is retried before Lucas is told, and how long the wait grows
# per attempt. Two attempts over ~24 s covers the overload blips seen in practice without leaving
# a turn apparently hung.
RETRIES = 2
RETRY_BACKOFF = 8.0


def _painter(msg, working, streaming: bool, lead: str = ""):
    """The live bubbles, or None when this turn is not streaming. The pin phrase is drawn ONCE
    here rather than per frame: re-rolling it every few seconds would make the line visibly
    flicker between wordings while Lucas is reading.

    `on_bubble` anchors each bubble the moment it is born rather than at the end of the turn,
    which is what makes AD-23 continuous under streaming (F4 Stage 3)."""
    result = None
    if streaming and working is not None:
        result = painter.Painter(working, phrases.pin(), origin=msg,
                                 on_bubble=_anchor_bubble, lead=lead)
    return result


def _anchor_bubble(bubble, session_id: str) -> None:
    msgmap.remember_reply(bubble.message_id, session_id)


async def guarded(coro, msg) -> None:
    """Run a turn as a detached task that cannot fail silently.

    Every turn is dispatched with `create_task`, so an exception inside one used to reach stderr
    and nothing else: Lucas sent a voice note and simply never heard back (2026-07-28). Nothing
    is retried here — the point is only that a turn which died SAYS so, in the chat, where the
    message that started it is."""
    try:
        await coro
    except Exception as e:
        print(f"turn failed: {e!r}")
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.ERROR_PHRASES, e=e)))


async def _speak(msg, text: str) -> None:
    """Best-effort voice reply (C5). Additive: the text is already delivered, so any failure here
    is logged and dropped rather than surfaced — it must never cost an answer Lucas already has."""
    try:
        spoken_text = speech.to_speech(text)
        speech_text = format.clip_chars(spoken_text, SPOKEN_CHARS)
        ogg_bytes = tts.synthesize(speech_text)
        await reply.send_voice(msg, ogg_bytes)
    except Exception as e:
        print(f"voice reply failed: {e}")


async def _dispatch(msg, working, prompt: str, *, session_id, backend_name, options, live, lead):
    """One turn, retried while the failure is transient AND nothing has reached the chat yet.

    Both halves matter. A 529 or a dropped connection is about the moment, not the request, and
    Lucas is usually not watching — letting one kill the turn costs him the whole task rather than
    a few seconds (2026-07-29). But once text has been painted, a retry would replay the answer on
    top of what he is already reading, so a mid-stream failure is reported instead of repeated."""
    on_text = live.paint if live is not None else None
    attempt = 0
    result = None
    while result is None:
        try:
            result = await dispatch.turn(prompt, session_id=session_id, backend_name=backend_name,
                                         cwd=WORKSPACE_DIR, options=options, on_text=on_text)
        except dispatch.DispatchError as e:
            shown = live is not None and bool(live.text)
            again = helpers.transient(e) and attempt < RETRIES and not shown
            if not again:
                await reply.deliver(working, msg, helpers.friendly_error(e), lead=lead)
                break
            attempt += 1
            note = lead + format.plain(phrases.pick(phrases.RETRY_PHRASES))
            await reply.edit_text(working, note)
            await asyncio.sleep(RETRY_BACKOFF * attempt)
    return result


async def run_and_deliver(msg, working, prompt: str, *, session_id: str | None,
                          backend_name: str, title: str | None, scope: str,
                          spoken: bool = False, lead: str = "") -> None:
    """Dispatch one turn with the scope's sticky knobs, then deliver the answer with its footer
    and the anchor keyboard. `spoken` (C5) additionally replies with a voice note synthesized from
    the same answer — text-triggered turns leave it False and are unaffected. `lead` is the quoted
    transcript a voice turn already showed, carried on so every bubble keeps it (AD-29) — and
    derived here when a caller did not pass it, so "a spoken turn quotes what was heard" holds for
    every entry point rather than for the two that remember."""
    if spoken and not lead:
        lead = answer.quote(prompt)
    options = helpers.turn_options(scope, title)
    live = _painter(msg, working, options.stream, lead)
    # The token is registered BEFORE the backend starts and released in the `finally` whatever
    # happens: an agent can call ask_user in its first second, and a token that outlived its turn
    # would leave a question waiting on a future nobody can resolve (F4 Stage 4).
    token = helpers.enable_ask(scope, backend_name, options)
    if token:
        ask.register(token, msg, live)
    try:
        result = await _dispatch(msg, working, prompt, session_id=session_id, live=live,
                                 backend_name=backend_name, options=options, lead=lead)
    finally:
        if token:
            ask.unregister(token)
    if result is None:
        return
    helpers.persist_turn(result.session_id, backend_name, title, result, options)
    # Only the text the painter has not already sealed above a question (AD-30).
    body = live.tail_of(result.text) if live is not None else result.text
    block = answer.block(body, result.session_id, title, provider=backend_name,
                         model=result.model, cost_usd=result.cost_usd, mode=options.mode,
                         context_used=result.context_used, context_window=result.context_window)
    markup = panelmenu.root_markup(result.session_id)
    if live is not None:
        # Bubbles the painter already sealed are final and on screen — delivering the whole
        # answer again would duplicate it, so only the live bubble onward is written.
        await live.note_session(result.session_id)
        sent = await live.finish(block, markup)
    else:
        sent = await reply.deliver(working, msg, block, reply_markup=markup, lead=lead)
    # Every bubble, not just the last: Lucas replies to whichever one he is reading (AD-23).
    # Idempotent, so re-anchoring one the painter already claimed costs nothing.
    for message in sent:
        msgmap.remember_reply(message.message_id, result.session_id)
    if spoken:
        await _speak(msg, result.text)


async def _working(msg, working, lead: str = ""):
    """The bubble the answer will be written into.

    A voice turn already put one on screen while it was transcribing, so it is morphed rather than
    joined by a second status message — and it is morphed to carry the TRANSCRIPT, which exists by
    now even though the answer does not (Lucas, 2026-07-29: seeing what was heard should not wait
    for the reply). The painter then keeps writing into this same bubble, lead included."""
    text = lead + format.plain(phrases.pick(phrases.WORKING_PHRASES))
    result = working
    if result is None:
        result = await reply.safe_reply(msg, text)
    else:
        await reply.edit_text(result, text)
    return result


async def start_new(msg, prompt: str, *, spoken: bool = False, working=None) -> None:
    """A new session runs on the NEW scope: whatever the last interaction used, minus anything
    the /new config bubble changed since."""
    lead = answer.quote(prompt) if spoken else ""
    working = await _working(msg, working, lead)
    title = format.title_from_prompt(prompt)
    harness = registry.harness_for(registry.NEW)
    await run_and_deliver(msg, working, prompt, session_id=None, backend_name=harness,
                          title=title, scope=registry.NEW, spoken=spoken, lead=lead)


async def handle_reply_continue(msg, sid: str, text: str, *, spoken: bool = False,
                                working=None) -> None:
    """`text` is the already-resolved prompt (msg.text for a text turn, the STT transcript for a
    voice turn) — read from the caller's arg, never re-derived from `msg.text`, since a voice
    message replying to a prior session anchor has no `.text` at all."""
    harness = registry.backend_for(sid) or registry.DEFAULT_BACKEND
    lead = answer.quote(text) if spoken else ""
    working = await _working(msg, working, lead)
    title = registry.title_for(sid)
    await run_and_deliver(msg, working, text, session_id=sid, backend_name=harness,
                          title=title, scope=sid, spoken=spoken, lead=lead)
