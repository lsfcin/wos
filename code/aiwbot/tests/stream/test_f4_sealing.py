# test_f4_sealing.py — F4 Stage 3: bubbles sealed as they are born, and the property that makes
# that safe. If the first test here fails, Stage 3 is wrong and Stage 2 still ships.
import asyncio
import random
from frontend.stream import painter
from frontend import reply
from frontend.text.htmlsplit import split_html
from ..chatkit import Bubble, Origin
from ..streamkit import Clock

_WORDS = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota"]


def _answer(paras: int, seed: int) -> str:
    rng = random.Random(seed)
    out = []
    for _ in range(paras):
        n = rng.randint(6, 45)
        out.append(" ".join(rng.choice(_WORDS) for _ in range(n)))
    return "\n\n".join(out)


def test_split_html_is_prefix_stable_at_line_boundaries():
    """THE load-bearing invariant of Stage 3. `split_html` is a single forward pass whose boundaries
    are decided only from lines already consumed, so appending text can change nothing but the
    LAST chunk. That is what lets a bubble be sealed and sent while the answer is still being
    written — without it, sealing would contradict AD-23 by rewriting bubbles Lucas has read."""
    violations = 0
    checked = 0
    for seed in range(25):
        full = _answer(30, seed)
        final = split_html(full, reply.TELEGRAM_MSG_LIMIT, reply.SOFT_CHARS)
        lines = full.split("\n")
        for i in range(1, len(lines) + 1):
            prefix = "\n".join(lines[:i])
            grown = split_html(prefix, reply.TELEGRAM_MSG_LIMIT, reply.SOFT_CHARS)
            if len(grown) < 2:
                continue
            checked += 1
            if grown[:-1] != final[:len(grown) - 1]:
                violations += 1
    assert checked > 200, f"only {checked} prefixes exercised — the corpus got too small"
    assert violations == 0


def _run(deltas, gap=10.0, seal=True):
    origin = Origin()
    working = Bubble(origin.chat)
    clock = Clock()
    anchored = []
    p = painter.Painter(working, "pensando…", clock=clock, origin=origin,
                        on_bubble=lambda b, sid: anchored.append(b), seal=seal)

    async def go():
        for d in deltas:
            clock.advance(gap)
            await p.paint(d, session_id="s1")

    asyncio.run(go())
    return p, origin, anchored


def _long_deltas(n=14):
    return [_answer(2, i) + "\n\n" for i in range(n)]


def test_a_growing_answer_is_sent_as_several_bubbles_while_it_streams():
    p, origin, _ = _run(_long_deltas())
    assert len(p.sent) > 1
    assert len(origin.sent) == len(p.sent) - 1


def test_a_bubble_is_never_touched_once_a_later_one_exists():
    """A bubble IS repainted while it is the live one — that is the whole feature. What must
    never happen is a write to it after it has been sealed by a successor being born: rewriting
    text Lucas has already read is the failure mode Stage 3 exists to avoid. Prefix-stability
    says its content cannot change; this proves we act on that."""
    p, origin, _ = _run(_long_deltas())
    assert len(p.sent) > 1, "the corpus did not produce a second bubble"
    born: set[int] = set()
    for action, mid in origin.chat.log:
        if action == "send":
            born.add(mid)
            continue
        later = [b for b in born if b > mid]
        assert not later, f"bubble {mid} was edited after {later} already existed"


def test_every_bubble_is_anchored_the_moment_it_is_born():
    """AD-23, and stronger than before: Lucas can reply to bubble 1 while bubble 3 is still
    being written, so anchoring cannot wait for the end of the turn."""
    p, _, anchored = _run(_long_deltas())
    assert len(anchored) == len(p.sent)
    assert [b.message_id for b in p.sent] == [m.message_id for m in anchored]


def test_only_the_live_bubble_carries_the_pin():
    p, _, _ = _run(_long_deltas())
    for bubble in p.sent[:-1]:
        assert "pensando" not in bubble.text
    assert p.sent[-1].text.endswith("pensando…")


def test_no_bubble_ever_exceeds_the_telegram_limit():
    p, _, _ = _run(_long_deltas(30))
    for bubble in p.sent:
        assert len(bubble.text) <= reply.TELEGRAM_MSG_LIMIT


def test_a_session_id_that_arrives_late_still_anchors_everything():
    """claude's system:init carries it before any text, but nothing may DEPEND on that."""
    origin = Origin()
    working = Bubble(origin.chat)
    clock = Clock()
    anchored = []
    p = painter.Painter(working, "pensando…", clock=clock, origin=origin,
                        on_bubble=lambda b, sid: anchored.append(b))

    async def go():
        for d in _long_deltas():
            clock.advance(10)
            await p.paint(d, session_id=None)

    asyncio.run(go())
    assert anchored == [], "nothing may be anchored before the session id is known"
    assert len(p.anchors.pending) == len(p.sent)
    asyncio.run(p.note_session("s1"))
    assert len(anchored) == len(p.sent)


def test_a_painter_with_nobody_listening_does_not_requeue_forever():
    """The pending drain used to iterate the very list `_anchor` appends to, so a painter built
    without `on_bubble` grew it without bound the moment a session id arrived — RAM until the OOM
    killer, which is how this was found (2026-07-28). Two independent fixes: the queue is
    snapshotted and cleared before the drain, and "nobody is listening" no longer re-queues."""
    origin = Origin()
    p = painter.Painter(Bubble(origin.chat), "pensando…", origin=origin)
    p.anchors.pending = [Bubble(origin.chat), Bubble(origin.chat)]
    asyncio.run(p.note_session("s1"))
    assert p.anchors.pending == []


def test_sealing_can_be_turned_off_without_touching_the_streaming_knob():
    """STREAM_SEAL is the Stage 3 rollback: it reverts to Stage 2's single frozen bubble while
    leaving streaming itself on."""
    p, origin, _ = _run(_long_deltas(), seal=False)
    assert len(p.sent) == 1
    assert origin.sent == []


def test_finish_lands_the_answer_without_duplicating_sealed_bubbles():
    """The integration boundary: bubbles the painter already sent are final and on screen, so the
    finished delivery must write only the live one onward. Re-sending them would post the answer
    twice, which is the obvious way this stage could go wrong in the chat and not in a test."""
    p, origin, _ = _run(_long_deltas())
    before = len(p.sent)
    body = p.text
    block = body + "\n· · ·\n[ABC] TITULO\nclaude · sonnet"

    sent = asyncio.run(p.finish(block, markup="KEYBOARD"))

    assert len(sent) >= before
    ids = [b.message_id for b in sent]
    assert len(set(ids)) == len(ids), "a bubble was delivered twice"
    assert "TITULO" in sent[-1].text
    assert all("TITULO" not in b.text for b in sent[:-1])
    for bubble in sent:
        assert "pensando" not in bubble.text, "the pin survived into the finished answer"
