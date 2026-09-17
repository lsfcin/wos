# test_markdown.py — free unit test: block + inline markdown -> Telegram HTML.
from frontend.text.markdown import format_body
from frontend.text.inline import convert


def test_h1_and_h2_are_bold_caps():
    assert format_body("# Achados") == "<b>ACHADOS</b>"
    assert format_body("## Achados") == "<b>ACHADOS</b>"


def test_h3_and_deeper_are_plain_bold():
    assert format_body("### Detalhe") == "<b>Detalhe</b>"
    assert format_body("#### Fundo") == "<b>Fundo</b>"


def test_heading_caps_keep_portuguese_accents():
    assert format_body("## Configuração") == "<b>CONFIGURAÇÃO</b>"


def test_bullets_become_glyphs_and_nest_one_level():
    assert format_body("- um") == "•  um"
    assert format_body("* dois") == "•  dois"
    assert format_body("  - aninhado") == "  ◦  aninhado"


def test_numbered_list_keeps_its_number():
    assert format_body("1. primeiro") == "1.  primeiro"


def test_blockquote_and_horizontal_rule():
    assert format_body("> citado") == "<blockquote>citado</blockquote>"
    assert format_body("---") == "─────"


def test_horizontal_rule_is_not_the_footer_separator():
    """`· · ·` already means 'the answer ends here' in every reply footer — a markdown rule
    reusing it would read as a second footer mid-message."""
    assert "·" not in format_body("---")


def test_link_becomes_anchor_with_escaped_url():
    out = format_body("[ex](https://e.com/a?b=1&c=2)")
    assert out == '<a href="https://e.com/a?b=1&amp;c=2">ex</a>'


def test_link_with_unsafe_scheme_is_left_as_text():
    assert format_body("[mau](javascript:alert(1))") == "[mau](javascript:alert(1))"


def test_italic_does_not_eat_bold():
    assert convert("**forte** e *leve*") == "<b>forte</b> e <i>leve</i>"


def test_underscores_inside_identifiers_survive():
    assert convert("snake_case_name") == "snake_case_name"


def test_strikethrough():
    assert convert("~~ido~~") == "<s>ido</s>"


def test_markdown_inside_inline_code_is_not_converted():
    """The code span is stashed before any other rule runs, so its contents reach Telegram
    exactly as the agent wrote them."""
    out = convert("veja `**nao_vira_bold**` aqui")
    assert out == "veja <code>**nao_vira_bold**</code> aqui"


def test_fenced_block_contents_untouched():
    out = format_body("```\n## nao e heading\n- nao e bullet\n```")
    assert "<b>" not in out
    assert "•" not in out
    assert out.startswith("<pre>")
