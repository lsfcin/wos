# askshape.py — what a question LOOKS like in the chat: its bubble, its keys, and how it closes.
#
# Split out of ask.py when registering the answer pushed that file past the size gate. The line the
# cut follows is the one the gate exposed: ask.py is the broker (tokens, futures, who is waiting),
# and this is the view (what Lucas reads and taps). Nothing here knows about a future.
from __future__ import annotations
from telegram import InlineKeyboardMarkup
from ..text import format
from ..select import keyboard
from .. import phrases, reply

# Tap payload: `a:<question id>:<index>`. The option TEXT never travels in it — callback_data has
# 64 bytes and an option is written by the agent, so only the index rides along and the text is
# read back from the question the broker is still holding.
TAP = "a:"
# What the chat shows when the wait ended without Lucas. The three sentences below go to the AGENT,
# not to him: they are what the tool call returns when nobody answered — text, never an MCP error,
# because an error aborts the turn and throws away everything it had worked out (Lucas 2026-07-27).
NO_ANSWER_NOTE = "sem resposta"
TIMEOUT_TEXT = ("sem resposta do usuário dentro do tempo de espera. siga com a hipótese mais "
                "razoável e diga explicitamente qual assumiu.")
ENDED_TEXT = "a conversa foi encerrada antes da resposta. siga sem ela."
EXPIRED_TEXT = "essa pergunta não pôde ser entregue ao usuário. siga sem ela."


def markup(question_id: str, options: list[str]):
    """Buttons only when the agent offered choices; a free-text reply always works as well.

    The buttons carry NUMBERS, not the options. An option is a phrase the agent wrote, Telegram
    truncates a label instead of wrapping it (AD-5), and clipping to a full-width button still cut
    real ones mid-word on Lucas's phone — "Cada mensagem vira sessão nov…" (live, 2026-07-29). So
    the phrase is listed in the message, where a newline works, and the key under it is its number:
    the same shape `/resume` settled on when it hit this wall. A number never truncates."""
    drawn = None
    if options:
        labels = [str(i + 1) for i in range(len(options))]
        cells = [keyboard.cell(label, f"{TAP}{question_id}:{i}") for i, label in enumerate(labels)]
        rows = keyboard.chunk(cells, keyboard.per_row(labels))
        drawn = InlineKeyboardMarkup(rows)
    return drawn


def _listed(options: list[str]) -> str:
    """The options in full, numbered so the keyboard has something to index into. Escaped: an
    option is arbitrary text the agent wrote, and one stray `<` would break the whole message."""
    lines = []
    for i, option in enumerate(options):
        body = format.plain(option)
        lines.append(f"{i + 1}. {body}")
    return "\n".join(lines)


def bubble_text(question: str, options: list[str]) -> str:
    """The question, then the choices in full, then how to answer when there are none. The hint is
    dropped once there are buttons: they say it themselves, and it would read like boilerplate."""
    body = format.plain(question)
    line = f"▸ {body}"
    if options:
        listed = _listed(options)
        line = f"{line}\n\n{listed}"
    else:
        line = f"{line}\n\n{phrases.ASK_HINT}"
    return line


def answer_note(answered: str) -> str:
    """What the CHAT shows as the answer. The three exits above are instructions to the model
    ("siga com a hipótese mais razoável"), never something Lucas said, so they collapse to a short
    note instead of being quoted back at him as if they were his words."""
    unanswered = (TIMEOUT_TEXT, ENDED_TEXT, EXPIRED_TEXT)
    shown = NO_ANSWER_NOTE if answered in unanswered else answered
    return shown


def _settled(sent: str) -> str:
    """The question as it should read once it HAS an answer: the "reply to this message" hint is
    an instruction, and leaving it under an answered question tells Lucas to do something already
    done. The choices stay — they are the record of what he was choosing between."""
    hint = f"\n\n{phrases.ASK_HINT}"
    text = sent
    if sent.endswith(hint):
        text = sent[:-len(hint)]
    return text


async def close(bubble, sent: str, answered: str) -> None:
    """The question stops being a question: its keyboard goes, so a later tap cannot pretend
    otherwise, and the answer is written into the same bubble, in italic, directly under what it
    answers (Lucas, live 2026-07-29 — "answers are not registered"). A question scrolled back to
    now says what was DECIDED, not only what was asked.

    Rebuilt from `sent`, never from the bubble: Telegram hands back the plain rendering of a
    message and never the HTML it was sent as (AD-30)."""
    if bubble is not None:
        note = answer_note(answered)
        shown = format.plain(note)
        asked = _settled(sent)
        text = f"{asked}\n\n<i>› {shown}</i>"
        await reply.edit_text(bubble, text, None)
