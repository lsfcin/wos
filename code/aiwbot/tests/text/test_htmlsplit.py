# test_htmlsplit.py — free unit test: chunking formatted HTML without breaking a tag.
from frontend.text.htmlsplit import split_html, strip_tags


def test_short_text_is_one_chunk():
    assert split_html("oi", 4096) == ["oi"]


def test_empty_text_still_yields_one_chunk():
    assert split_html("", 4096) == [""]


def _long_pre(lines: int) -> str:
    body = "\n".join(f"linha {i} de codigo" for i in range(lines))
    return f"<pre>{body}</pre>"


def test_open_tag_is_closed_and_reopened_across_the_boundary():
    """The bug this exists for: the old splitter cut every 4096 chars blind to tags, so a
    cut inside <pre> produced HTML Telegram rejects — and the message was silently dropped."""
    chunks = split_html(_long_pre(40), 200)
    assert len(chunks) > 1
    for chunk in chunks[:-1]:
        assert chunk.endswith("</pre>")
    for chunk in chunks[1:]:
        assert chunk.startswith("<pre>")


def test_every_chunk_respects_the_limit():
    chunks = split_html(_long_pre(40), 200)
    for chunk in chunks:
        assert len(chunk) <= 200


def test_anchor_href_survives_the_reopen():
    text = '<a href="https://e.com">' + "\n".join("palavra" for _ in range(60)) + "</a>"
    chunks = split_html(text, 120)
    assert len(chunks) > 1
    assert chunks[1].startswith('<a href="https://e.com">')


def test_one_line_longer_than_a_whole_chunk_is_sliced_safely():
    chunks = split_html("<b>" + "x" * 900 + "</b>", 200)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200
        assert chunk.count("<") == chunk.count(">")


def test_unbalanced_closer_does_not_raise():
    """Agent text is not guaranteed well-formed; dropping the message is worse than
    tolerating a stray closing tag."""
    chunks = split_html("</b>solto", 4096)
    assert chunks == ["</b>solto"]


def test_strip_tags_unescapes_entities():
    assert strip_tags("<b>a &amp; b</b>") == "a & b"


def test_strip_tags_keeps_link_label_not_url():
    assert strip_tags('<a href="http://x">rotulo</a>') == "rotulo"
