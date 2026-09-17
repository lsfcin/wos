# test_b1_table_bold.py — regression spec for [b1]: tables and bold not rendering in Telegram.
#
# Both halves of the report came from constructs found in REAL agent answers (BUGS asked
# for exactly that), not from hand-written shapes: a pipe-table with markdown in its cells, and
# the `**bold *italic***` run whose crossed tags made Telegram strip a whole message's markup.
import re
from frontend.text.markdown import format_body
from frontend.text.inline import convert

_TAG = re.compile(r"<(/?)([a-zA-Z-]+)(?:\s[^>]*)?>")


def _crossed(html: str) -> bool:
    """Telegram rejects a message whose entities cross or dangle — and reply.py's fallback
    then strips EVERY tag, so one bad run costs the whole answer its formatting."""
    stack = []
    bad = False
    for match in _TAG.finditer(html):
        closing = match.group(1)
        name = match.group(2)
        if not closing:
            stack.append(name)
            continue
        if not stack or stack[-1] != name:
            bad = True
            break
        stack.pop()
    return bad or bool(stack)


# --- half one: a table's cells are markdown, and <pre> froze them into literal asterisks ---

def test_bold_inside_a_table_cell_actually_renders():
    text = "| Constraint | Requirement |\n|---|---|\n| Low rate limit | **Batched units.** N items. |"
    out = format_body(text)
    assert "<b>Batched units.</b>" in out
    assert "**" not in out


def test_a_table_is_never_boxed_in_pre():
    text = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = format_body(text)
    assert "<pre>" not in out


def test_code_and_links_in_cells_survive_too():
    text = "| Stage | Detail |\n|---|---|\n| F2 | `bote` and [docs](https://x.dev) |"
    out = format_body(text)
    assert "<code>bote</code>" in out
    assert '<a href="https://x.dev">docs</a>' in out


def test_three_column_rows_label_their_values_but_two_column_rows_do_not():
    wide = "| Stage | Contents | Why |\n|---|---|---|\n| F1 | bugs | first |"
    narrow = "| Stage | Contents |\n|---|---|\n| F1 | bugs |"
    assert "Contents: bugs" in format_body(wide)
    assert "Contents: bugs" not in format_body(narrow)
    assert "<b>F1</b>\nbugs" in format_body(narrow)


def test_an_already_bold_first_cell_is_not_double_wrapped():
    text = "| Stage | Why |\n|---|---|\n| **F1** | first |"
    out = format_body(text)
    assert "<b><b>" not in out
    assert "<b>F1</b>" in out


# --- half two: `**bold *italic***` crossed its tags, costing the message ALL formatting ---

def test_bold_wrapping_italic_does_not_cross_its_tags():
    # Verbatim from a real answer (transcript b366e3e6), the shape that triggered the report.
    out = convert("- **anything isoroll *visual*** (I3 golden layer) — eyeball gate.")
    assert not _crossed(out)
    assert "<b>anything isoroll <i>visual</i></b>" in out


def test_triple_asterisks_nest_bold_and_italic():
    out = convert("***both***")
    assert not _crossed(out)
    assert out == "<b><i>both</i></b>"


def test_ordinary_bold_and_italic_are_untouched_by_the_fix():
    assert convert("**bold**") == "<b>bold</b>"
    assert convert("*ital*") == "<i>ital</i>"
    assert convert("**a** and **b**") == "<b>a</b> and <b>b</b>"
    assert convert("snake_case_name") == "snake_case_name"
