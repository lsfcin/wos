# test_format.py — free unit test: markdown/table -> Telegram HTML conversion.
from frontend.stream import answer
from frontend.text.format import format_body, session_block, reattach_cmd, title_words, title_from_prompt, response_preview, relative_time, short_model, clip_chars, PREVIEW_CHARS, TITLE_CHARS


def test_plain_markdown_to_html():
    out = format_body("**bold** and `code`")
    assert out == "<b>bold</b> and <code>code</code>"


def test_pipe_table_becomes_row_blocks_not_a_pre_box():
    text = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = format_body(text)
    assert "<pre>" not in out
    assert out.startswith("<b>a · b</b>")
    assert "<b>1</b>\n2" in out


def test_fenced_code_block_boxed_as_pre():
    out = format_body("before\n```\nraw <text>\n```\nafter")
    assert "<pre>\nraw &lt;text&gt;\n</pre>" in out
    assert "before" in out
    assert "after" in out


def test_title_words_defaults_when_empty():
    assert title_words(None) == "(SEM TÍTULO)"
    assert title_words("  ") == "(SEM TÍTULO)"


def test_session_block_includes_header_and_body():
    block = session_block("Pronto.", "abc12345", "hello world session", body="oi")
    assert "Pronto." in block
    assert "[ABC]" in block
    assert "HELLO WORLD SESSION" in block
    assert "oi" in block


def test_reattach_cmd_per_backend():
    # AD-8: bot sessions are resumable by id but never listed in Claude Code's picker,
    # so the copyable command is the only way to open one outside the bot.
    assert reattach_cmd("sid-1", "claude") == "claude --resume sid-1"
    assert reattach_cmd("sid-1", "opencode") == "opencode -s sid-1"


def test_reattach_cmd_unknown_backend_is_none():
    assert reattach_cmd("sid-1", None) is None
    assert reattach_cmd("sid-1", "nope") is None


def test_session_block_offers_copyable_reattach_command():
    block = session_block("Pronto.", "abc12345", "t", backend="claude")
    assert "<code>claude --resume abc12345</code>" in block


def test_session_block_omits_reattach_without_backend():
    block = session_block("Pronto.", "abc12345", "t")
    assert "<code>" not in block


def test_title_from_prompt_takes_leading_words():
    title = title_from_prompt("revisa o arquivo de configuração agora por favor com calma", n=4)
    assert title == "revisa o arquivo de"


def test_response_preview_head_and_tail():
    text = "um dois tres quatro cinco seis sete oito nove dez onze doze treze"
    assert response_preview(text) == "um dois tres quatro cinco seis … oito nove dez onze doze treze"


def test_response_preview_short_text_untouched():
    assert response_preview("resposta curta") == "resposta curta"


def test_clip_chars_leaves_text_at_the_limit_alone():
    assert clip_chars("12345", 5) == "12345"


def test_clip_chars_ellipsis_replaces_the_overflow():
    assert clip_chars("123456", 5) == "12345…"


def test_title_is_capped_in_chars_too():
    long_words = "supercalifragilistico expialidoso extraordinario absurdo"
    title = title_words(long_words, 5)
    assert len(title) <= TITLE_CHARS + 1


def test_response_preview_capped_in_chars_not_only_words():
    """A 6…6-word preview still runs 25-140 chars depending on word length, which is what
    made the picker bubble resize between pages. The character cap is the real budget."""
    text = " ".join(f"palavralonga{i}" for i in range(20))
    preview = response_preview(text)
    assert len(preview) <= PREVIEW_CHARS + 1
    assert preview.endswith("…")


def test_relative_time_buckets():
    now = 1_000_000.0
    assert relative_time(now - 10, now) == "agora"
    assert relative_time(now - 300, now) == "5m atrás"
    assert relative_time(now - 7200, now) == "2h atrás"
    assert relative_time(now - 259200, now) == "3d atrás"


def test_short_model_extracts_family():
    assert short_model("claude-sonnet-5") == "sonnet"
    assert short_model("claude-opus-4-8") == "opus"
    assert short_model(None) is None
    assert short_model("gpt-4o") == "gpt-4o"


def test_answer_body_first_then_the_footer_that_names_it():
    """Footer is TWO lines (Lucas, 2026-07-27): which session, then what it ran on. Run
    together the title was hard to pick out of the meta."""
    block = answer.block("oi tudo bem", "abc12345", "titulo da sessao",
                         provider="claude", model="claude-sonnet-5", cost_usd=0.022)
    lines = block.split("\n")
    assert lines[0] == "oi tudo bem"
    assert "· · ·" in block
    assert lines[-2] == "[ABC] TITULO DA SESSAO"
    assert lines[-1] == "claude · sonnet · $0.022"


def test_answer_footer_omits_missing_meta():
    block = answer.block("resposta", "abc12345", None, provider="opencode", model=None, cost_usd=None)
    lines = block.split("\n")
    assert lines[-2] == "[ABC] (SEM TÍTULO)"
    assert lines[-1] == "opencode"
