# answer.py — the shape of one answer message: the agent's text, then the footer that names it.
from __future__ import annotations
import html
from ..text import SESSION_ID_LABEL_LEN, clip_chars, format_body, meta_bits, title_words
from ..text import split_html, strip_tags

SEPARATOR = "· · ·"
# Slack so a chunk sized with the pin still fits once the pin is swapped for the footer.
_PIN_MARGIN = 16
# Room for the ` (12/12)` a bubble ends with.
_COUNT_MARGIN = 10
# A voice note can run for minutes; its transcript opens every bubble of the answer, so it is
# clipped to something that reads as a reminder of the question rather than as the message.
LEAD_CHARS = 300
# `block` wants the whole answer as one string and lets reply.deliver do the splitting, so it
# calls `frames` with a limit nothing can reach.
_UNBOUNDED = 10 ** 9
# The footer names the session, and three words was too terse to recognise a turn by (Lucas,
# 2026-07-27). Its own char budget too: unlike the /resume picker, a footer line has no bubble
# width to keep stable, so it can afford the whole five words.
TITLE_WORDS = 5
TITLE_CHARS = 48


def _meta_line(provider: str | None, model: str | None, cost_usd: float | None,
               mode: str | None, used: int | None = None, window: int | None = None) -> str:
    bits = meta_bits(provider, model, mode, used, window)
    if cost_usd:
        bits.append(f"${cost_usd:.3f}")
    return " · ".join(bits)


def _session_label(sid: str | None, title: str | None) -> str | None:
    """`[ABC] TÍTULO DA SESSÃO`, or nothing when there is no session to name."""
    result = None
    if sid:
        short = sid[:SESSION_ID_LABEL_LEN].upper()
        words = title_words(title, TITLE_WORDS, TITLE_CHARS)
        result = f"[{short}] {words}"
    return result


def _footer(sid: str | None, title: str | None, provider: str | None, model: str | None,
            cost_usd: float | None, mode: str | None, used: int | None,
            window: int | None) -> list[str]:
    """Two lines, not one (Lucas, 2026-07-27): which session this is, then what it ran on.
    They answer different questions, and running them together made the title hard to find."""
    label = _session_label(sid, title)
    meta = _meta_line(provider, model, cost_usd, mode, used, window)
    return [bit for bit in (label, meta) if bit]


def quote(transcript: str) -> str:
    """What the bot heard, as the opening line of every bubble of the answer to it.

    It used to be a bubble of its own, sent before the turn ran (F2). Lucas, 2026-07-28: *"eu
    gostava quando a transcrição aparecia dentro do bubble... a transcrição não teria uma bubble
    só para si"* — a standalone echo costs a message, and a long answer left it scrolled far
    above the part being read. Repeated per bubble, the answer always says what it is answering.
    Clipped, because a two-minute voice note would otherwise open every bubble with a wall."""
    text = clip_chars(transcript.strip(), LEAD_CHARS)
    escaped = html.escape(text)
    return f'<blockquote><i>"{escaped}"</i></blockquote>\n'


def _counter(index: int, total: int | None) -> str:
    """`(2/3)` when the answer is finished and `(2)` while it is still arriving: mid-stream the
    total is genuinely unknown — bubble 3 exists only once the text that fills it does — and a
    sealed bubble is never rewritten to correct it (AD-25). So the count that is knowable is
    shown, and the last bubble of a finished answer is the one that carries the total."""
    label = f"({index}/{total})" if total else f"({index})"
    return label


def _with_counter(body: str, counter: str) -> str:
    """The counter closes the ANSWER, so it lands on the last line of the text — before the footer
    when this chunk carries one, and hard against the final word rather than adrift on a line of
    its own (Lucas, 2026-07-29: it had drifted below `· · ·` and onto the next line)."""
    head, sep, tail = body.rpartition("\n" + SEPARATOR)
    if sep:
        placed = f"{head.rstrip()} {counter}{sep}{tail}"
    else:
        placed = f"{body.rstrip()} {counter}"
    return placed


def decorate(chunks: list[str], lead: str = "", total: int | None = None,
             start: int = 1) -> list[str]:
    """Put the per-bubble furniture on chunks that are already split: the quoted transcript at
    the top, the position at the end. Both are omitted when they would say nothing — no lead
    without a voice note, no count for an answer that is one bubble. `start` numbers a chunk that
    is being restamped on its own, out of the list it originally came from."""
    counted = max(total or 0, len(chunks)) > 1
    out = []
    for index, chunk in enumerate(chunks, start=start):
        body = f"{lead}{chunk}" if lead else chunk
        if counted:
            counter = _counter(index, total)
            body = _with_counter(body, counter)
        out.append(body)
    return out


def room(limit: int, lead: str = "", pin: str | None = None) -> int:
    """The budget left for the answer's own text once its furniture is accounted for. Reserved
    up front rather than trimmed afterwards: a chunk that fits only until the footer replaces the
    pin is a message Telegram rejects at the moment the turn ends."""
    return limit - len(pin or "") - len(lead) - _PIN_MARGIN - _COUNT_MARGIN


def _drop_blank_tail(chunks: list[str]) -> list[str]:
    """A text that ends on a paragraph break splits with a whitespace-only chunk at the end, and
    mid-stream that becomes a BUBBLE holding nothing but its counter and the pin (seen 2026-07-29).
    Only the last one is dropped, and only when something else survives: it is the chunk still
    growing, so removing it cannot disturb a bubble already on screen."""
    kept = chunks
    if len(chunks) > 1:
        bare = strip_tags(chunks[-1])
        if not bare.strip():
            kept = chunks[:-1]
    return kept


def bare_frames(settled: str, unsettled: str = "", pin: str | None = None,
                footer: list[str] | None = None, limit: int = 4096,
                soft: int | None = None, lead: str = "") -> list[str]:
    """The split, WITHOUT the per-bubble furniture. Kept separate because a bubble has to be
    recorded undecorated: restamping a chunk that already carries `(1)` produces `(1) (1/10)`
    (seen 2026-07-29), so the counter can only ever be applied to this."""
    rendered = format_body(settled) if settled.strip() else ""
    parts = [rendered]
    if unsettled.strip():
        parts.append(html.escape(unsettled))
    for line in footer or []:
        parts.append(html.escape(line))
    text = "\n".join(part for part in parts if part)
    chunks = split_html(text, room(limit, lead, pin), soft)
    return _drop_blank_tail(chunks)


def frames(settled: str, unsettled: str = "", pin: str | None = None,
           footer: list[str] | None = None, limit: int = 4096, soft: int | None = None,
           lead: str = "", start: int = 1) -> list[str]:
    """The bubbles an answer occupies right now — mid-stream or finished.

    `settled` is markdown that can no longer change and so is rendered; `unsettled` is the
    tail still arriving, appended as escaped plain text because rendering it would make it
    flicker between literal and formatted as the closing markers land. `pin` (the ⏳ line) rides
    at the very END of the last bubble so it reads as "still going", and the split budget is
    reduced by it so a finished frame can never overflow when the pin is later removed.

    Finished delivery is the degenerate case — no pin, footer present — which is why `block`
    delegates here: the streamed frames and the shipped answer are the same code path, and that
    is what makes the AD-23 non-regression test meaningful rather than a coincidence."""
    bare = bare_frames(settled, unsettled, pin, footer, limit, soft, lead)
    chunks = decorate(bare, lead, start=start)
    if pin:
        # A blank line of distance, so the pin reads as a status hanging under the answer rather
        # than as the answer's next line (Lucas, 2026-07-27).
        chunks[-1] = chunks[-1] + "\n\n" + pin
    return chunks


def block(body: str, sid: str | None, title: str | None, provider: str | None = None,
          model: str | None = None, cost_usd: float | None = None,
          mode: str | None = None, context_used: int | None = None,
          context_window: int | None = None) -> str:
    """The agent's answer, then meta: `[ID] TÍTULO · provider · modelo · modo · X% · $custo`.

    F2 led every answer with a `continua [ABC] TÍTULO` line, reasoning that Telegram quotes a
    message from its start, so the session name had to come first. Sound reasoning, wrong
    reader: the bot's answer is already `do_quote`d onto Lucas's own message, so the thread is
    visible without being announced. Lucas, 2026-07-27: *"quando o bot responde a mim, como já
    mostra que é uma resposta, acho que pode deixar assim"*, and *"o título pode ficar no
    rodapé, fica melhor"*. The anchor line is deleted rather than demoted — the id and title
    survive in the footer, which is where he wanted them."""
    footer = _footer(sid, title, provider, model, cost_usd, mode, context_used, context_window)
    tail = [SEPARATOR] + footer
    # An answer that ends on a paragraph break would put a blank line between its last words and
    # the separator, which the splitter reads as a place to break — leaving the footer alone in a
    # bubble of its own (seen 2026-07-29). The footer belongs to the last bubble that has text.
    body = body.rstrip()
    # Delegates to `frames` at an unbounded limit, so it comes back as exactly one chunk and
    # `reply.deliver` still does the splitting. The point is that the finished answer and a
    # streamed frame are then literally the same code path, which is what makes the AD-23
    # non-regression check meaningful instead of two implementations that merely agree today.
    whole = frames(body, footer=tail, limit=_UNBOUNDED)
    return whole[0]


