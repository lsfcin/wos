# test_hotwords.py — free unit test: hotwords is explicit editable data (C4), not inline in stt.py.
from frontend.voice import hotwords


def test_hotwords_is_a_nonempty_list_of_strings():
    assert isinstance(hotwords.HOTWORDS, list)
    assert len(hotwords.HOTWORDS) > 0
    assert all(isinstance(w, str) and w for w in hotwords.HOTWORDS)


def test_as_prompt_joins_every_hotword_into_one_string():
    prompt = hotwords.as_prompt()
    assert isinstance(prompt, str)
    for word in hotwords.HOTWORDS:
        assert word in prompt
