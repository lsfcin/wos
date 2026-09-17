# landing.py — turn the live bubbles into the finished answer: the footer, the keyboard, and the
#
# one pass that stamps every bubble with its exact position. Split out of painter.py (2026-07-29,
# size gate): painting is what happens WHILE the answer arrives, landing is what happens once it
# has. Both halves work on the same `Painter`, which is passed in rather than inherited from.
from __future__ import annotations
from . import answer
from .. import reply
from ..text import split_html


async def land(live, block: str, markup=None) -> list:
    """Write the finished answer onto the bubbles already on screen.

    `block` is only the CURRENT segment's text plus the footer (see `Painter.tail_of`): everything
    before it is sealed above a question and final, so re-rendering it here would post the answer a
    second time. The footer and keyboard land on the last chunk, and the pin is gone because
    `block` never had one."""
    budget = answer.room(reply.TELEGRAM_MSG_LIMIT, live.lead)
    bare = split_html(block, budget, reply.SOFT_CHARS)
    sealed = live.bubbles.sealed()
    total = sealed + len(bare)
    chunks = answer.decorate(bare, live.lead, total=total, start=sealed + 1)
    written = len(live.sent) - 1
    for i, chunk in enumerate(chunks):
        last = i == len(chunks) - 1
        tail_markup = markup if last else None
        if i < len(live.sent):
            await live.bubbles.write(live.sent[i], chunk, tail_markup, bare=bare[i])
        elif i > written:
            opened = await live.bubbles.open(chunk, tail_markup, bare=bare[i])
            if opened is None:
                break
    await stamp(live, total)
    return list(live.answers)


async def stamp(live, total: int) -> None:
    """One closing pass so every bubble ends `(2/3)` instead of the `(2)` it was born with (Lucas
    asked for exact positions everywhere, 2026-07-28).

    This is the ONE moment a sealed bubble is rewritten, and why the rule reads "a sealed bubble is
    not rewritten *while the answer is streaming*" rather than "never": the total cannot exist
    before the end, and only the counter changes — nothing already read moves. It runs last, so the
    answer completes first and the stamping trails it. Bubbles from earlier segments are included,
    which is why `bubbles.bare` records what each one holds undecorated: Telegram hands back the
    plain rendering of a message, never the HTML that was sent, and stamping a chunk that already
    carries `(1)` would produce `(1) (1/10)`."""
    for index, bubble in enumerate(live.answers, start=1):
        original = live.bubbles.bare.get(bubble.message_id)
        if original is None:
            continue
        stamped = answer.decorate([original], live.lead, total=total, start=index)[0]
        await live.bubbles.write(bubble, stamped, bare=original)
