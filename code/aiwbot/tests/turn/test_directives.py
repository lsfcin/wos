# test_directives.py — F3a: read leading harness/model words off a bot-prefixed message, $0.
# The index is fixed here so the test neither shells opencode nor reads its sqlite — it pins
# the PARSING, and backend_names() (used for harness self-aliases) is pure, no I/O.
import pytest
from frontend.turn import directives

_INDEX = [
    ("claude", "sonnet"), ("claude", "opus"), ("claude", "fable"),
    ("opencode", "nvidia/z-ai/glm-5.2"), ("opencode", "nvidia/deepseek-v4-flash"),
    ("opencode", "moonshotai/kimi-k3-instruct"),
]


@pytest.fixture(autouse=True)
def _fixed_index(monkeypatch):
    monkeypatch.setattr(directives, "_index_cache", list(_INDEX))
    monkeypatch.setattr(directives, "_harness_cache", None)


def test_a_harness_then_a_model_are_both_read_off_the_front():
    harness, model, rest = directives.resolve("opencode glm resume o pdf")
    assert harness == "opencode"
    assert model == "nvidia/z-ai/glm-5.2"
    assert rest == "resume o pdf"


def test_a_model_alone_implies_its_harness():
    harness, model, rest = directives.resolve("sonnet escreve o resumo")
    assert harness == "claude"
    assert model == "sonnet"
    assert rest == "escreve o resumo"


def test_a_substring_matches_the_model_segment_past_the_provider_path():
    _, model, _ = directives.resolve("deepseek analisa o log")
    assert model == "nvidia/deepseek-v4-flash"


def test_a_spoken_alias_resolves_to_the_registered_harness():
    harness, model, rest = directives.resolve("cc roda os testes")
    assert harness == "claude"
    assert model is None
    assert rest == "roda os testes"


def test_a_directive_word_only_counts_at_the_very_front():
    """The whole point of the safety rule: `opus` in the middle of a sentence is prose."""
    harness, model, rest = directives.resolve("escreve sobre opus dei")
    assert harness is None
    assert model is None
    assert rest == "escreve sobre opus dei"


def test_a_harness_named_first_pins_the_model_search_to_it():
    """`claude glm` cannot resolve glm (an opencode model), so glm stays in the prompt."""
    harness, model, rest = directives.resolve("claude glm faz algo")
    assert harness == "claude"
    assert model is None
    assert rest == "glm faz algo"


def test_an_explicit_harness_and_model_both_land():
    harness, model, rest = directives.resolve("claude opus explica isso")
    assert harness == "claude"
    assert model == "opus"
    assert rest == "explica isso"


def test_a_leading_comma_is_not_part_of_the_word():
    harness, _, rest = directives.resolve("opencode, resume aqui")
    assert harness == "opencode"
    assert rest == "resume aqui"


def test_a_task_less_message_is_left_untouched():
    """Every word was a directive, so there is no prompt — reconfiguring silently here is never
    what was meant, so nothing is applied and the text is returned whole."""
    harness, model, rest = directives.resolve("sonnet")
    assert harness is None
    assert model is None
    assert rest == "sonnet"


def test_plain_prose_resolves_to_nothing():
    harness, model, rest = directives.resolve("resume o documento que mandei ontem")
    assert harness is None
    assert model is None
    assert rest == "resume o documento que mandei ontem"


def test_a_two_letter_token_is_too_short_to_be_a_model():
    """Guards against stray hits; harness aliases like `cc` are matched separately, not here."""
    found = directives._model_match("v4", None)
    assert found == (None, None)
