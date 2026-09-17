# test_resume.py — free unit test: /resume picker list/label/pagination assembly.
import time
from frontend.session.resume import _entry_line, _list_text, _header, _meta, _keyboard, _ruler

_NOW = time.time()


def test_meta_line_order_is_provider_model_mode_context_when():
    item = {"backend": "claude", "updated_at": _NOW, "mode": "plan", "model": "claude-sonnet-5",
            "context_used": 320_000, "context_window": 1_000_000}
    assert _meta(item) == "claude · sonnet · plan · 32% · agora"


def test_meta_line_omits_missing_mode_model_and_context():
    item = {"backend": "opencode", "updated_at": _NOW}
    assert _meta(item) == "opencode · agora"


def test_meta_line_omits_context_without_known_window():
    item = {"backend": "claude", "updated_at": _NOW, "context_used": 320_000, "context_window": None}
    assert _meta(item) == "claude · agora"


def test_entry_line_three_lines_with_preview():
    item = {"title": "hello world session", "preview": "faz isso e a resposta fica pronta agora",
            "backend": "claude", "updated_at": _NOW, "mode": "plan", "model": "claude-sonnet-5"}
    line = _entry_line(1, item)
    expected = ("1. HELLO WORLD SESSION\n"
                "faz isso e a resposta fica pronta agora\n"
                "claude · sonnet · plan · agora")
    assert line == expected


def test_entry_line_omits_preview_when_absent():
    item = {"title": "hello world session", "preview": None, "backend": "claude", "updated_at": _NOW}
    line = _entry_line(2, item)
    assert line == "2. HELLO WORLD SESSION\nclaude · agora"


def test_title_caps_at_five_words():
    item = {"title": "one two three four five six seven eight", "preview": None,
            "backend": "claude", "updated_at": _NOW}
    line = _entry_line(1, item)
    assert line.startswith("1. ONE TWO THREE FOUR FIVE\n")


def test_list_text_blank_line_between_entries():
    items = [{"title": "a", "preview": None, "backend": "claude", "updated_at": _NOW},
              {"title": "b", "preview": None, "backend": "opencode", "updated_at": _NOW}]
    text = _list_text(items)
    assert text == "1. A\nclaude · agora\n\n2. B\nopencode · agora"


# `_clip` is gone (F5b). The anchor no longer truncates its body at an arbitrary 3000 chars —
# that clip, not Telegram's 4096 limit, is what produced the mid-word "[…]" Lucas reported. It
# now goes through reply.deliver like an answer: split on paragraph boundaries, nothing dropped.


def test_header_counts_shown_of_total():
    # the "/resume N pra ver todas" hint is gone: « / » arrows page through instead
    assert _header(12, 5, "") == "Sessões recentes — 5 de 12"


def test_header_no_hint_when_all_shown():
    assert _header(3, 3, "") == "Sessões recentes — 3 de 3"


def test_keyboard_is_single_row_of_numerals_between_arrows():
    items = [{"session_id": "sid-a", "title": "a", "backend": "claude", "updated_at": _NOW},
              {"session_id": "sid-b", "title": "b", "backend": "opencode", "updated_at": _NOW}]
    markup = _keyboard(items)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["«", "1", "2", "»"]
    assert [b.callback_data for b in row[1:-1]] == ["resume:sid-a", "resume:sid-b"]


def _items(n, start=0):
    return [{"session_id": f"sid-{i}", "title": "t", "backend": "claude", "updated_at": _NOW}
            for i in range(start, start + n)]


def test_keyboard_row_shape_is_identical_on_every_page():
    """The bubble stopped resizing because the row never changes width: five slots always,
    whichever end of the range you are on."""
    shapes = []
    for offset in (0, 3, 6):
        markup = _keyboard(_items(3, offset), offset=offset, query="", total=9)
        row = markup.inline_keyboard[0]
        shapes.append(len(row))
    assert shapes == [5, 5, 5]


def test_keyboard_first_page_back_arrow_is_inert():
    markup = _keyboard(_items(3), offset=0, query="", total=9)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["«", "1", "2", "3", "»"]
    assert row[0].callback_data == "noop:"
    assert row[-1].callback_data == "page:3:"


def test_keyboard_middle_page_has_both_arrows_live_and_absolute_numerals():
    markup = _keyboard(_items(3), offset=3, query="", total=9)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["«", "4", "5", "6", "»"]
    assert row[0].callback_data == "page:0:"
    assert row[-1].callback_data == "page:6:"


def test_keyboard_last_page_next_arrow_is_inert():
    markup = _keyboard(_items(3), offset=6, query="", total=9)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["«", "7", "8", "9", "»"]
    assert row[0].callback_data == "page:3:"
    assert row[-1].callback_data == "noop:"


def test_keyboard_arrows_carry_the_active_filter():
    markup = _keyboard(_items(3), offset=0, query="bugfix", total=9)
    row = markup.inline_keyboard[0]
    assert row[-1].callback_data == "page:3:bugfix"


def test_ruler_is_monospace_nbsp_of_fixed_width():
    from frontend.session.resume import RULER_WIDTH
    ruler = _ruler()
    assert ruler.startswith("\n<code>")
    assert ruler.count(" ") == RULER_WIDTH


def test_list_text_numbers_from_page_offset():
    text = _list_text(_items(2), start=4)
    assert text.startswith("4. T\n")
    assert "\n\n5. T\n" in text
