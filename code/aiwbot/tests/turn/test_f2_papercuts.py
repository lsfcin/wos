# test_f2_papercuts.py — the F2 batch: phrase tone, flat glyphs, the reply anchor, and the
# "bote" mishearing. Each choice below was made by Lucas against a live Telegram prototype
# (2026-07-26), so these tests pin decisions, not guesses.
from frontend import phrases
from frontend.turn.startword import strip_prefix
from frontend.stream import answer

_BANKS = [phrases.CAPTURE_ACKS, phrases.WORKING_PHRASES, phrases.NEW_EMPTY_PROMPT_PHRASES,
          phrases.ERROR_PHRASES, phrases.UNKNOWN_CMD_PHRASES,
          phrases.SESSION_LIVE_ELSEWHERE_PHRASES, phrases.RESUME_EMPTY_PHRASES,
          phrases.RESUME_ANCHOR_PHRASES, phrases.TRANSCRIBE_FAIL_PHRASES]


# --- tone: lowercase, no trailing period (Lucas: "B") ---

def test_no_bank_phrase_ends_in_a_period():
    for bank in _BANKS:
        for phrase in bank:
            assert not phrase.endswith("."), phrase


def test_no_bank_phrase_starts_with_a_capital():
    """A chat ack is an aside, not a sentence. Placeholders like {cmd} are exempt — what
    they interpolate is a command name, not prose."""
    for bank in _BANKS:
        for phrase in bank:
            first = phrase[0]
            assert first == first.lower(), phrase


# --- glyphs: flat, not gradient emoji (Lucas: "B") ---

def test_status_phrases_carry_no_gradient_emoji():
    for phrase in phrases.WORKING_PHRASES:
        assert "⏳" not in phrase


def test_no_phrase_opens_with_the_divider_glyph():
    """`·` separates (`· · ·`, `provider · modelo`), so it cannot also open a line — Lucas,
    2026-07-28: "o · nunca deveria ir no começo, é um divisor"."""
    banks = [phrases.WORKING_PHRASES, phrases.CAPTURE_ACKS, phrases.ERROR_PHRASES,
             phrases.TRANSCRIBE_FAIL_PHRASES, phrases.RESUME_ANCHOR_PHRASES,
             phrases.NEW_EMPTY_PROMPT_PHRASES, [phrases.ASK_HINT, phrases.pin()]]
    for bank in banks:
        for phrase in bank:
            assert not phrase.startswith("·"), phrase


# --- the reply anchor: REVERSED by Lucas 2026-07-27, see F5c and answer.block's docstring.
# F2's leading `continua [ABC] …` line is gone; the session is named in the footer instead.
# These stay as the record of what was tried and what replaced it.

def test_the_answer_opens_with_the_answer():
    block = answer.block("corpo da resposta", "abc12345", "titulo da sessao")
    assert block.split("\n")[0] == "corpo da resposta"
    assert "continua" not in block


def test_the_session_is_named_once_in_the_footer():
    block = answer.block("corpo", "abc12345", "titulo", provider="claude")
    assert block.count("[ABC]") == 1
    assert block.split("\n")[-2] == "[ABC] TITULO"


def test_an_answer_without_a_session_names_none():
    block = answer.block("corpo", None, None, provider="claude")
    assert "[" not in block
    assert block.split("\n")[0] == "corpo"


# --- "bote": the mishearing that swallowed the session-start intent ---

def test_the_misheard_bote_starts_a_session_like_bot_does():
    assert strip_prefix("bote roda os testes") == "roda os testes"
    assert strip_prefix("bote, roda os testes") == "roda os testes"


def test_the_real_start_word_still_works():
    assert strip_prefix("bot roda os testes") == "roda os testes"
    assert strip_prefix("bot, roda os testes") == "roda os testes"
    assert strip_prefix("BOT roda") == "roda"


def test_a_word_merely_beginning_with_bot_is_not_a_start_word():
    assert strip_prefix("botar isso no inbox") is None
    assert strip_prefix("botequim amanha") is None
    assert strip_prefix("nada a ver") is None
