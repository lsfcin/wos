# test_voice_echo_and_picker.py — Lucas's 2026-07-27 live test: STT conditioning prompt shape,
# the transcript echo, and a picker that stops reshuffling itself under his thumb.
from frontend.stream import answer
from frontend.voice import hotwords
from frontend.select import panelmenu
from frontend import phrases
from frontend.turn import startword
from ..panelkit import texts as _texts

# Longest run of words the prompt may go without a punctuation mark. The bug was a 26-word bare
# list; real sentences in Lucas's register sit well under this.
_MAX_UNPUNCTUATED_RUN = 12


def _longest_unpunctuated_run(text: str) -> int:
    longest = 0
    run = 0
    for word in text.split():
        marks = [ch for ch in word if ch in ",.?!:;"]
        if marks:
            run = 0
        else:
            run += 1
            longest = max(longest, run)
    return longest


def test_the_conditioning_prompt_is_prose_with_no_bare_word_list():
    """The whole 2026-07-27 finding in one assertion: a bare word list anywhere in the prompt
    suppresses punctuation (measured 0.0 marks/100 words against 22.5 without it). Appending
    HOTWORDS to the sentences is the regression this guards."""
    prompt = hotwords.as_prompt()
    assert _longest_unpunctuated_run(prompt) <= _MAX_UNPUNCTUATED_RUN


def test_the_prompt_ends_on_a_sentence():
    assert hotwords.as_prompt().rstrip()[-1] in ".?!"


def test_every_carrier_sentence_is_punctuated():
    for sentence in hotwords.CARRIER:
        assert sentence.rstrip()[-1] in ".?!"


def test_the_models_lucas_says_out_loud_are_in_the_vocabulary():
    """`claude sonnet` came back as `claudsonner` because no model name was primed at all,
    which silently cost the F3a spoken directive too."""
    for name in ("claude", "sonnet", "opus", "fable", "haiku"):
        assert name in hotwords.HOTWORDS


def test_the_echo_is_italic_quotes_and_carries_no_label():
    """Still italic inside quotes and still label-free (Lucas, 2026-07-27), but it is no longer a
    message of its own: since 2026-07-28 it opens every bubble of the answer, so it lives in
    `answer.quote` and the standalone `TRANSCRIPT_ECHO` phrase is gone."""
    line = answer.quote("oi")
    assert '<i>"oi"</i>' in line
    assert "ouvi" not in line


def test_a_misheard_bote_opener_is_normalized_before_it_is_echoed():
    """Echoing `bote` while routing already treated it as `bot` reported a solved problem."""
    assert startword.normalize("bote, roda os testes") == "bot, roda os testes"
    assert startword.normalize("Bote me ajuda") == "bot me ajuda"


def test_normalize_leaves_a_message_that_never_opened_with_the_word_alone():
    assert startword.normalize("o bote virou") == "o bote virou"
    assert startword.normalize("bot, tudo certo") == "bot, tudo certo"


def _shortlist(values, current):
    markup = panelmenu.values_markup("m", values, current)
    return [label.strip("[ ]") for label in _texts(markup)]


def test_a_selection_that_already_fits_does_not_reshuffle_the_row():
    """Lucas: picking fable/sonnet/opus reordered the buttons every time. They all fit on the
    row, so there was nothing to rescue — the motion was noise."""
    models = ["sonnet", "opus", "fable"]
    first = _shortlist(models, None)
    for chosen in models:
        assert _shortlist(models, chosen) == first, chosen


def test_a_selection_that_would_fall_off_the_row_is_still_hoisted():
    """The reordering exists for a reason: a picker that hides what is set is worse than one
    that reorders. Long lists keep that behaviour."""
    models = [f"m{i}" for i in range(12)]
    shown = _shortlist(models, "m9")
    assert "m9" in shown


def test_a_selection_missing_from_the_list_entirely_still_leads():
    """Picked from the `all` drill-down, so it is not in the shortlist at all."""
    shown = _shortlist(["sonnet", "opus"], "openrouter/qwen/qwen3")
    assert any("qwen" in label for label in shown)
