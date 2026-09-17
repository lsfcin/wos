# ask.py — the bot side of ask_user: hold a running turn open on a question until Lucas answers.
# The agent's tool call blocks inside the daemon (askserver hands it here), so an answer resumes
# the SAME turn rather than starting a new one — that is the whole point of the MCP round trip.
from __future__ import annotations
import asyncio
import secrets
from dataclasses import dataclass, field
from . import askshape
from ..session import msgmap
from .. import phrases, reply
# The chat shape lives in askshape (size gate). Re-exported so `ask.TAP` / `ask.TIMEOUT_TEXT` keep
# resolving: the broker is what the rest of the bot talks to, and the split is internal to it.
from .askshape import (EXPIRED_TEXT, ENDED_TEXT, NO_ANSWER_NOTE, TAP,  # noqa: F401
                       TIMEOUT_TEXT)

# Lucas asked for about an hour to answer, away from the PC (2026-07-27). The CLI's own ceiling
# on a tool call is raised past this in ClaudeBackend.env(), so this wait is the one that ends
# first and an unanswered question comes back as OUR text rather than as the CLI's timeout.
WAIT_SECONDS = 55 * 60


@dataclass
class _Question:
    token: str
    future: asyncio.Future
    options: list[str] = field(default_factory=list)
    bubble: object | None = None
    # What was SENT, kept because Telegram hands back the plain rendering of a message and never
    # the HTML it was sent as (AD-30). Rewriting the bubble from its echo would drop the markup.
    text: str = ""


# token -> (the message a question is sent as a reply to, the turn's painter or None). One entry
# per LIVE turn: registered in runner before the backend is called and dropped in its `finally`,
# so a token can never outlive the turn that owns it.
_TURNS: dict[str, tuple] = {}
# question id -> the question still waiting for an answer.
_QUESTIONS: dict[str, _Question] = {}


def new_token() -> str:
    """Per-turn, unguessable, and short: it is spent in a URL the CLI is pointed at."""
    return secrets.token_hex(4)


def register(token: str, msg, live=None) -> None:
    """`live` is the turn's painter, when it has one: a question has to close the bubble above it
    before it is posted, or text written after the question would keep growing that bubble and end
    up ABOVE the thing it answers (Lucas, 2026-07-29)."""
    _TURNS[token] = (msg, live)


def unregister(token: str) -> None:
    """End of the turn. Anything still waiting on this token is released here and now — a future
    nobody will ever resolve would leak a task per turn, and the tool call blocking on it would
    sit there until the CLI's own ceiling."""
    _TURNS.pop(token, None)
    stale = [qid for qid, item in _QUESTIONS.items() if item.token == token]
    for qid in stale:
        answer(qid, ENDED_TEXT)


def question_of(message_id: int) -> str | None:
    """Which unanswered question this message is asking, if any. Answered ones are dropped from
    the live map, so a reply to an old question bubble falls through to normal routing."""
    qid = msgmap.ask_question(message_id)
    live = qid if qid in _QUESTIONS else None
    return live


def answer(question_id: str, text: str) -> bool:
    """Resolve a waiting question. False when there is nothing to resolve — an evicted map entry,
    a question already answered, or a tap on a keyboard whose turn has ended."""
    item = _QUESTIONS.get(question_id)
    open_now = item is not None and not item.future.done()
    if open_now:
        item.future.set_result(text)
    return open_now


def answer_tap(data: str) -> bool:
    """A tapped button: `a:<question id>:<index>` back into the option text it stands for."""
    parts = data.split(":")
    resolved = False
    if len(parts) == 3:
        item = _QUESTIONS.get(parts[1])
        index = int(parts[2]) if parts[2].isdigit() else -1
        if item is not None and 0 <= index < len(item.options):
            resolved = answer(parts[1], item.options[index])
    return resolved


async def handle_callback(update, context) -> None:
    """PTB entry point for `a:` taps. The toast is the only feedback the tap itself gives — the
    real answer is the turn resuming and writing more text."""
    query = update.callback_query
    taken = answer_tap(query.data)
    note = phrases.ASK_TAKEN if taken else phrases.ASK_STALE
    await query.answer(text=note)


async def _wait(item: _Question) -> str:
    try:
        answered = await asyncio.wait_for(item.future, WAIT_SECONDS)
    except asyncio.TimeoutError:
        answered = TIMEOUT_TEXT
    return answered


async def _hold(origin, token: str, question: str, options: list[str]) -> str:
    qid = secrets.token_hex(3)
    loop = asyncio.get_running_loop()
    item = _Question(token=token, future=loop.create_future(), options=options)
    _QUESTIONS[qid] = item
    item.text = askshape.bubble_text(question, options)
    keys = askshape.markup(qid, options)
    item.bubble = await reply.safe_reply(origin, item.text, reply_markup=keys)
    answered = EXPIRED_TEXT
    if item.bubble is not None:
        msgmap.remember_ask(item.bubble.message_id, qid)
        answered = await _wait(item)
    _QUESTIONS.pop(qid, None)
    await askshape.close(item.bubble, item.text, answered)
    return answered


async def ask(token: str, question: str, options: list[str] | None = None) -> str:
    """Put the question in the chat and block the agent's tool call until it is answered.

    Every exit is a string, including the ones nobody answered: this return value goes straight
    back into the running turn, where an exception would end it instead."""
    turn = _TURNS.get(token)
    answered = EXPIRED_TEXT
    if turn is not None:
        origin, live = turn
        if live is not None:
            # Seal what is on screen and drop the pin: the answer so far is complete as far as
            # Lucas is concerned, and the status line must not claim work that is blocked on him.
            await live.cut()
        answered = await _hold(origin, token, question, list(options or []))
    return answered
