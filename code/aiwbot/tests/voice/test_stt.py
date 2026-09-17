# test_stt.py — free unit test: STT wrapper (C1 transcription, C3 fail-safe, C6 no live calls).
import pathlib
from frontend.voice import stt

# Confident enough to keep. Real transcripts of Lucas's voice notes measured -0.153..-0.482.
_GOOD = -0.3
# What whisper scored on near-silent audio it hallucinated words for (measured: -1.489).
_BAD = -1.5


class FakeSegment:
    def __init__(self, text, avg_logprob=_GOOD):
        self.text = text
        self.avg_logprob = avg_logprob


class FakeModel:
    """Stands in for faster_whisper.WhisperModel: transcribe(path, …) -> (segments, info).
    No real model load, no audio decode — a fixture, not a live call."""

    def __init__(self, segments):
        self._segments = segments
        self.calls = []

    def transcribe(self, path, language="pt", initial_prompt=None, **kw):
        self.calls.append({"path": path, "language": language,
                           "initial_prompt": initial_prompt, **kw})
        return iter(self._segments), None


def test_run_joins_segment_texts_and_primes_with_the_prompt():
    model = FakeModel([FakeSegment(" oi"), FakeSegment(" tudo bem")])
    text = stt.run(pathlib.Path("/tmp/x.ogg"), model, hotwords="Bot, roda os testes. aiwbot")
    assert text.strip() == "oi tudo bem"
    assert model.calls[0]["initial_prompt"] == "Bot, roda os testes. aiwbot"


def test_the_jargon_rides_in_initial_prompt_not_the_hotwords_arg():
    """The two compete for the same conditioning slot; priming for punctuation via a separate
    `hotwords=` arg cost the vocabulary ("bote" came back as "Pode")."""
    model = FakeModel([FakeSegment("oi")])
    stt.run(pathlib.Path("/tmp/x.ogg"), model, hotwords="aiwbot")
    assert model.calls[0].get("hotwords") is None
    assert model.calls[0]["vad_filter"] is True


def test_transcribe_lazily_loads_model_and_prompt(monkeypatch):
    model = FakeModel([FakeSegment("oi bot")])
    monkeypatch.setattr(stt, "_model", lambda: model)
    monkeypatch.setattr("frontend.voice.hotwords.as_prompt", lambda: "Bot, roda. aiwbot")
    result = stt.transcribe(pathlib.Path("/tmp/x.ogg"))
    assert result.strip() == "oi bot"


def test_transcribe_returns_empty_string_on_exception(monkeypatch):
    class BoomModel:
        def transcribe(self, *a, **kw):
            raise RuntimeError("decode failed")

    monkeypatch.setattr(stt, "_model", lambda: BoomModel())
    result = stt.transcribe(pathlib.Path("/tmp/bad.ogg"))
    assert result == ""


# --- F3b: whisper invents words on near-silent audio, and no decoding setting stops it ---

def test_a_transcript_the_model_itself_doubts_is_rejected():
    """Dispatching hallucinated text costs a real turn; "" rides the C3 fail-safe instead."""
    model = FakeModel([FakeSegment("e-mail.com", avg_logprob=_BAD)])
    text = stt.run(pathlib.Path("/tmp/silence.ogg"), model, hotwords="aiwbot")
    assert text == ""


def test_a_confident_transcript_is_kept():
    model = FakeModel([FakeSegment("bot, roda os testes", avg_logprob=_GOOD)])
    text = stt.run(pathlib.Path("/tmp/x.ogg"), model, hotwords="aiwbot")
    assert text == "bot, roda os testes"


def test_confidence_is_the_mean_so_one_weak_segment_does_not_sink_a_turn():
    segments = [FakeSegment("uma frase longa e clara", avg_logprob=-0.2),
                FakeSegment(" e um fim abafado", avg_logprob=-1.2)]
    assert stt.confident(segments) is True


def test_no_segments_at_all_is_not_confident():
    assert stt.confident([]) is False
