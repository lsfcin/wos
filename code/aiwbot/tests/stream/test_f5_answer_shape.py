# test_f5_answer_shape.py — F5: a long answer arrives as several repliable bubbles.
# Lucas, INBOX 2026-07-26: "partir a resposta em várias mensagens pra parecer mais como uma
# conversação, desde que me permitisse, respondendo qualquer uma delas, continuar na mesma sessão."
import asyncio
from frontend.stream import answer
from frontend import reply
from frontend.text.htmlsplit import split_html, strip_tags

_PARA = "Uma frase que ocupa algum espaço na mensagem e segue adiante."


def _paragraphs(n: int) -> str:
    return "\n\n".join(f"{_PARA} ({i})" for i in range(n))


class _FakeSent:
    def __init__(self, message_id):
        self.message_id = message_id


class _FakeMsg:
    """Records every bubble the delivery sent, in order."""

    def __init__(self):
        self.sent = []

    async def reply_text(self, text, parse_mode=None, do_quote=False, reply_markup=None):
        self.sent.append(text)
        return _FakeSent(100 + len(self.sent))


def test_a_long_answer_is_split_even_though_it_fits_in_one_telegram_message():
    """The whole point of F5b: splitting is a UX choice, not only a 4096 rescue."""
    text = _paragraphs(20)
    assert len(text) < 4096
    chunks = split_html(text, 4096, reply.SOFT_CHARS)
    assert len(chunks) > 1


def test_a_short_answer_is_still_a_single_bubble():
    chunks = split_html("resposta curta", 4096, reply.SOFT_CHARS)
    assert len(chunks) == 1


def test_no_chunk_is_empty_or_whitespace_only():
    """Telegram rejects an empty message, and runs of blank lines used to be able to seal one."""
    text = "primeiro\n\n\n\n\n" + _paragraphs(20) + "\n\n\n\n"
    for chunk in split_html(text, 4096, reply.SOFT_CHARS):
        assert strip_tags(chunk).strip()


def test_a_chunk_ends_at_a_paragraph_break_not_mid_sentence():
    for chunk in split_html(_paragraphs(20), 4096, reply.SOFT_CHARS)[:-1]:
        assert chunk.rstrip().endswith(")")


def test_the_hard_limit_still_wins_over_the_soft_one():
    """One paragraph with no break in it must still be cut to fit Telegram's cap."""
    for chunk in split_html("x" * 9000, 4096, reply.SOFT_CHARS):
        assert len(chunk) <= 4096


def test_open_tags_survive_a_soft_split_too():
    text = "<b>abre\n\n" + _paragraphs(20) + "\n\nfecha</b>"
    chunks = split_html(text, 4096, reply.SOFT_CHARS)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.count("<b>") == chunk.count("</b>")


def test_nothing_is_dropped_across_the_split():
    text = _paragraphs(20)
    joined = "".join(strip_tags(c) for c in split_html(text, 4096, reply.SOFT_CHARS))
    for i in range(20):
        assert f"({i})" in joined


def test_deliver_returns_every_bubble_so_they_can_all_be_anchored():
    """F5a: anchoring only the tail is what made a reply to an earlier bubble fall through to
    INBOX capture instead of continuing the session."""
    msg = _FakeMsg()
    sent = asyncio.run(reply.deliver(None, msg, _paragraphs(20)))
    assert len(sent) == len(msg.sent)
    assert len(sent) > 1
    ids = [m.message_id for m in sent]
    assert len(set(ids)) == len(ids)


def test_the_footer_rides_the_last_bubble():
    """So the session label and cost are not stranded in the middle of the conversation."""
    block = answer.block(_paragraphs(20), "abc12345", "titulo", provider="claude")
    chunks = split_html(block, 4096, reply.SOFT_CHARS)
    assert "[ABC]" in chunks[-1]
    assert answer.SEPARATOR in chunks[-1]


def test_the_footer_title_runs_to_five_words():
    """Three words was too terse to recognise a turn by (Lucas, 2026-07-27). The /resume picker
    keeps its own tighter budget, because there the cap exists to stop the bubble resizing."""
    block = answer.block("corpo", "abc12345", "explica o ciclo da agua em quatro paragrafos",
                         provider="claude")
    label = block.split("\n")[-2]
    assert label == "[ABC] EXPLICA O CICLO DA AGUA"
    assert len(label.split()) == 1 + 5


def test_the_resume_picker_title_budget_is_unchanged():
    from frontend.text.format import title_words, TITLE_CHARS
    assert title_words("um dois tres quatro cinco seis") == "UM DOIS TRES"
    assert len(title_words("palavralonga " * 6, 5)) <= TITLE_CHARS + 1
