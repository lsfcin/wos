# test_speech.py — free unit test: markdown answer -> prose a TTS voice can read (F3b).
from frontend.voice.speech import to_speech


def test_html_entities_come_back_as_characters():
    """The old path ran html.escape over the answer, so Kokoro was handed `&#x27;` to say."""
    out = to_speech("O script do Lucas&#x27;s faz A &amp; B &lt;aqui&gt;")
    assert "&" not in out.replace("A & B", "")
    assert "Lucas's" in out
    assert "A & B" in out


def test_emphasis_markers_vanish_but_their_words_stay():
    out = to_speech("Rodei os testes e **2 quebraram**, o *terceiro* passou")
    assert "*" not in out
    assert "2 quebraram" in out
    assert "terceiro" in out


def test_headings_and_bullets_lose_their_punctuation_marks():
    out = to_speech("## Resultado\n\n- primeiro\n- segundo")
    assert "#" not in out
    assert not out.startswith("-")
    assert "primeiro" in out


def test_a_table_is_named_once_however_many_rows_it_had():
    table = "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n| 5 | 6 |"
    out = to_speech(table)
    assert out.count("tabela") == 1
    assert "|" not in out


def test_a_code_fence_is_named_not_spelled_out():
    out = to_speech("antes\n\n```python\nprint(1)\n```\n\ndepois")
    assert "print(1)" not in out
    assert "trecho de código" in out
    assert "antes" in out
    assert "depois" in out


def test_a_link_keeps_its_label_and_drops_its_url():
    out = to_speech("veja [o log](https://ci.example.com/run/1) agora")
    assert "o log" in out
    assert "https" not in out


def test_a_bare_url_becomes_the_word_link():
    out = to_speech("está em https://example.com/x/y/z ok")
    assert "https" not in out
    assert "link" in out


def test_inline_code_keeps_the_word_inside_it():
    out = to_speech("roda `make test` agora")
    assert "`" not in out
    assert "make test" in out


def test_long_blank_runs_collapse_so_the_voice_does_not_stall():
    out = to_speech("uma coisa\n\n\n\n\noutra coisa")
    assert "\n\n" not in out
    assert "uma coisa" in out
    assert "outra coisa" in out


def test_ordinary_prose_survives_untouched():
    prose = "Rodei os testes, dois quebraram. Quer que eu conserte?"
    assert to_speech(prose) == prose
