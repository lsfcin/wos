# stt.py — speech-to-text boundary: faster-whisper large-v3-turbo, lazy-loaded; fails safe to "" .
# Priming is the CALLER's data — a domain passes its own carrier prose to `run`, because the
# prompt is what buys both vocabulary and punctuation, and no two domains share one.
from __future__ import annotations
import pathlib

_MODEL_NAME = "large-v3-turbo"
# Whisper hallucinates on near-silent audio, and no decoding setting stops it: on one of Lucas's
# empty voice notes the plain prompt emitted "... ... ...", the jargon-primed one invented
# "e-mail e-mail e-mail", and enabling VAD only shortened that to "e-mail.com". What DOES
# separate them is the model's own confidence. Measured across all 15 of his voice notes, every
# real transcript scored between -0.153 and -0.482 while that garbage scored -1.489, so the
# threshold sits between with room on both sides. (`no_speech_prob` was 0.000 for every file,
# real or not — VAD strips the silence it would have keyed on, so it is not a usable signal.)
_MIN_LOGPROB = -0.9
_cached_model = None


def model():
    """Lazy-cached WhisperModel. faster_whisper is imported *inside* here, never at module
    top, so a test can import this module without the (heavy, optional) dep installed."""
    global _cached_model
    if _cached_model is None:
        from faster_whisper import WhisperModel
        _cached_model = WhisperModel(_MODEL_NAME, device="cpu", compute_type="int8")
    return _cached_model


def confident(segments: list) -> bool:
    """Did the model believe what it just wrote? Mean avg_logprob over the segments."""
    result = False
    if segments:
        total = sum(s.avg_logprob for s in segments)
        mean = total / len(segments)
        result = mean >= _MIN_LOGPROB
    return result


def run(path: pathlib.Path, whisper, hotwords: str, lang: str = "pt") -> str:
    """Transcribe one file with an injectable model — the test boundary. Any failure (bad audio,
    model error) degrades to "" rather than raising: the fail-safe invariant. A transcript the
    model itself doubts degrades the same way."""
    text = ""
    try:
        segments, _info = whisper.transcribe(str(path), language=lang, initial_prompt=hotwords,
                                             vad_filter=True)
        listed = list(segments)
        joined = "".join(seg.text for seg in listed)
        if confident(listed):
            text = joined
        else:
            print(f"stt.run rejected a low-confidence transcript: {joined[:80]!r}")
    except Exception as e:
        print(f"stt.run failed: {e}")
        text = ""
    return text.strip()
