# tts.py — TTS wrapper: Kokoro-82M pf_dora voice, lazy-loaded; local OGG/Opus encode (C5, C6).
from __future__ import annotations
import io
import numpy as np
import soundfile as sf

_VOICE = "pf_dora"
_LANG_CODE = "p"  # pt-br, per kokoro's ALIASES table
_SAMPLE_RATE = 24000
_cached_pipeline = None


def _pipeline():
    """Lazy-cached Kokoro KPipeline. kokoro is imported *inside* here, never at module top,
    so make test can import this module without the (heavy, optional) dep installed."""
    global _cached_pipeline
    if _cached_pipeline is None:
        from kokoro import KPipeline
        _cached_pipeline = KPipeline(lang_code=_LANG_CODE)
    return _cached_pipeline


def encode_ogg(samples, sample_rate: int = _SAMPLE_RATE) -> bytes:
    """Pure, unit-testable with a synthetic numpy waveform — no model load needed."""
    buf = io.BytesIO()
    sf.write(buf, samples, sample_rate, format="OGG", subtype="OPUS")
    return buf.getvalue()


def synthesize(text: str) -> bytes:
    pipeline = _pipeline()
    chunks = [audio for _graphemes, _phonemes, audio in pipeline(text, voice=_VOICE) if audio is not None]
    samples = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    return encode_ogg(samples, _SAMPLE_RATE)
