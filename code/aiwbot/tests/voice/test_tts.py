# test_tts.py — free unit test: TTS wrapper (C5 voice reply) + local OGG/Opus encode (C6, no live calls).
import numpy as np
from frontend.voice import tts


def test_encode_ogg_produces_a_real_ogg_container():
    samples = np.zeros(2400, dtype=np.float32)  # 0.1s of silence @ 24kHz — no live model needed
    ogg_bytes = tts.encode_ogg(samples, sample_rate=24000)
    assert isinstance(ogg_bytes, bytes)
    assert ogg_bytes[:4] == b"OggS"


def test_synthesize_uses_pipeline_voice_pf_dora_and_encodes(monkeypatch):
    calls = []

    class FakePipeline:
        """Stands in for Kokoro's KPipeline: callable, yields (graphemes, phonemes, audio)."""

        def __call__(self, text, voice="pf_dora"):
            calls.append((text, voice))
            return [(None, None, np.zeros(240, dtype=np.float32))]

    monkeypatch.setattr(tts, "_pipeline", lambda: FakePipeline())
    out = tts.synthesize("olá mundo")
    assert isinstance(out, bytes)
    assert calls == [("olá mundo", "pf_dora")]
