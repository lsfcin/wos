# test_f4_frames.py — F4 Stage 2: what may be RENDERED mid-stream, and the guarantee that a
# streamed turn still ends as byte-for-byte the answer today's code ships.
from frontend.stream import answer
from frontend.text import markdown
from frontend import reply
from frontend.text.htmlsplit import split_html


# --- what may be rendered mid-stream ---------------------------------------------------------

def test_only_text_that_can_no_longer_change_is_rendered():
    """A half-typed `**bold` renders literal now and flips once the closing stars land, so it
    stays in the unsettled tail until a paragraph break proves it finished."""
    settled, tail = markdown.stable_prefix("pronto aqui.\n\nmeio de uma frase **negr")
    assert settled.strip() == "pronto aqui."
    assert "**negr" in tail


def test_an_unclosed_code_fence_makes_every_later_break_unsafe():
    """Inside a fence a blank line is not a paragraph boundary, it is part of the code."""
    text = "intro.\n\n```python\nx = 1\n\ny = 2\n"
    settled, tail = markdown.stable_prefix(text)
    assert settled.strip() == "intro."
    assert "```" in tail


def test_a_closed_fence_is_settled_again():
    text = "intro.\n\n```\nx = 1\n```\n\ndepois"
    settled, tail = markdown.stable_prefix(text)
    assert "```" in settled
    assert tail.strip() == "depois"


def test_a_frame_never_exceeds_telegram_even_with_the_pin():
    chunks = answer.frames("x " * 4000, "", pin="· pensando…")
    for chunk in chunks:
        assert len(chunk) <= reply.TELEGRAM_MSG_LIMIT


# --- the AD-23 non-regression ---------------------------------------------------------------

def test_a_streamed_turn_still_ends_as_exactly_todays_answer():
    """`block` delegates to `frames`, so the finished answer and a streamed frame are the same
    code path. This pins that they agree, byte for byte, through the real delivery split."""
    body = "\n\n".join(f"Paragrafo {i} com algum conteudo real." for i in range(12))
    block = answer.block(body, "abc12345", "titulo da sessao", provider="claude",
                         model="claude-sonnet-5", cost_usd=0.02, mode="build")
    delivered = split_html(block, reply.TELEGRAM_MSG_LIMIT, reply.SOFT_CHARS)
    footer = [answer.SEPARATOR, "[ABC] TITULO DA SESSAO", "claude · sonnet · build · $0.020"]
    streamed = answer.frames(body, "", pin=None, footer=footer,
                             limit=reply.TELEGRAM_MSG_LIMIT, soft=reply.SOFT_CHARS)
    assert streamed == delivered


