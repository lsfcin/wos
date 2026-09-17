# test_f6_interview_shape.py — what the chat looks like when the agent interviews Lucas mid-turn
#
# (2026-07-29, from his first real interview). A question is its own message, so everything the
# agent writes after it has to land BELOW it — the answer to a question must never appear above the
# question — and the status line must not sit there claiming work that is blocked on him.
import asyncio
from frontend.stream import painter
from ..chatkit import Bubble, Origin
from ..streamkit import Clock

_PARA = "palavra " * 60 + "\n\n"


def _turn(before: int = 6, after: int = 6, gap: float = 10.0):
    """Stream `before` paragraphs, have a question interrupt, then stream `after` more."""
    origin = Origin()
    clock = Clock()
    live = painter.Painter(Bubble(origin.chat), "pensando…", clock=clock, origin=origin,
                           on_bubble=lambda b, sid: None)

    async def go():
        for i in range(before):
            clock.advance(gap)
            await live.paint(f"antes {i} " + _PARA, session_id="s1")
        sealed = list(live.sent)
        await live.cut()
        for i in range(after):
            clock.advance(gap)
            await live.paint(f"depois {i} " + _PARA, session_id="s1")
        return sealed

    sealed = asyncio.run(go())
    return live, origin, sealed


def test_text_written_after_a_question_lands_in_a_new_bubble():
    """The whole point: the bubble that was live when the question went out is closed, so the text
    that answers the question appears under it rather than growing it from above."""
    live, _, sealed = _turn()
    assert live.sent, "nothing was written after the question"
    for bubble in live.sent:
        assert bubble not in sealed
        assert "depois" in bubble.text


def test_a_bubble_closed_by_a_question_is_never_written_again():
    live, origin, sealed = _turn()
    closed = {bubble.message_id for bubble in sealed}
    born_after = [mid for action, mid in origin.chat.log if action == "send" and mid not in closed]
    assert born_after, "no bubble was opened after the cut"
    first_new = born_after[0]
    seen_new = False
    for action, mid in origin.chat.log:
        if mid == first_new:
            seen_new = True
        if seen_new and action == "edit":
            assert mid not in closed, f"bubble {mid} was rewritten after the question"


def test_the_status_line_leaves_the_bubble_a_question_closes():
    """Lucas: with a question waiting there is no need for "pensando…" — and worse, it claims to be
    working on something that is actually blocked on him."""
    live, _, sealed = _turn()
    assert sealed, "the corpus produced no sealed bubble"
    assert "pensando" not in sealed[-1].text


def test_the_pin_moves_to_whatever_is_last():
    """The status belongs on the newest bubble, wherever that now is."""
    live, _, _ = _turn()
    assert live.sent[-1].text.endswith("pensando…")


def test_a_status_bubble_with_no_answer_in_it_is_removed():
    """A question asked before the agent wrote anything leaves a bubble holding nothing but
    "trabalhando…". It is deleted rather than left above the question."""
    origin = Origin()
    working = Bubble(origin.chat)
    live = painter.Painter(working, "pensando…", clock=Clock(), origin=origin)
    asyncio.run(live.cut())
    assert working.deleted is True
    assert working not in live.answers


def test_the_count_runs_across_the_whole_answer_not_per_segment():
    """Bubbles are numbered over the answer, so the interview does not restart the count at 1 after
    every question — and the questions themselves are not counted, they are not answer text."""
    live, _, _ = _turn()
    block = live.text + "\n· · ·\n[ABC] TITULO"
    sent = asyncio.run(live.finish(block))
    total = len(sent)
    assert total > 2, "the corpus did not produce enough bubbles"
    for index, bubble in enumerate(sent, start=1):
        assert f"({index}/{total})" in bubble.text, bubble.text[-60:]


def test_the_counter_closes_the_answer_and_the_footer_stays_last():
    """Lucas, 2026-07-29: the count had drifted below `· · ·` and onto a line of its own. It closes
    the ANSWER, so the footer comes after it."""
    live, _, _ = _turn()
    block = live.text + "\n· · ·\n[ABC] TITULO\nclaude · sonnet"
    sent = asyncio.run(live.finish(block))
    tail = sent[-1].text
    counter = f"({len(sent)}/{len(sent)})"
    assert counter in tail
    assert tail.index(counter) < tail.index("· · ·")
    assert tail.rstrip().endswith("claude · sonnet")
    assert f"\n{counter}" not in tail, "the counter is adrift on its own line"


def _finished():
    from frontend.stream import answer
    live, origin, sealed = _turn()
    block = answer.block(live.tail_of(live.text), "abc12345", "TITULO",
                         provider="claude", model="sonnet")
    sent = asyncio.run(live.finish(block))
    return live, sent


def test_the_answer_is_not_posted_a_second_time_below_the_questions():
    """The closing pass re-renders only what the painter has not sealed. Handing it the WHOLE answer
    reposted everything written before the question underneath it (caught by eyeballing, 2026-07-29
    — every assertion in this file passed while it was happening)."""
    live, sent = _finished()
    joined = "".join(bubble.text for bubble in sent)
    assert joined.count("antes 0") == 1
    assert joined.count("depois 0") == 1


def test_a_restamped_bubble_does_not_grow_a_second_counter():
    """A bubble is recorded undecorated, so stamping the total cannot append `(1/7)` after the
    `(1)` it was born with."""
    live, sent = _finished()
    total = len(sent)
    for index, bubble in enumerate(sent, start=1):
        assert bubble.text.count(f"({index}/{total})") == 1
        assert f"({index}) " not in bubble.text


def test_the_footer_never_gets_a_bubble_of_its_own():
    """An answer ending on a paragraph break left a blank line before `· · ·`, which the splitter
    read as a place to break — so the session line arrived alone in the last bubble."""
    live, sent = _finished()
    tail = sent[-1].text
    body = tail.split("· · ·")[0]
    assert body.strip(), "the footer landed in a bubble with no answer text"
