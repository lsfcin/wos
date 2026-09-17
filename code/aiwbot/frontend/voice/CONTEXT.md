# voice
> The audio-in-out pipeline: what the bot hears, and what it says back.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: the audio-in-out pipeline: what the bot hears, and what it says back. |
| [`hotwords.py`](hotwords.py) | [`hotwords.pyi`](hotwords.pyi) | `as_prompt` | hotwords.py — explicit editable data (C4): what the STT is primed with before it listens. Kept as data, not inline in stt.py, so it can be tuned without touching wrapper logic. |
| [`speech.py`](speech.py) | [`speech.pyi`](speech.pyi) | `to_speech` | speech.py — an agent's markdown answer -> prose a TTS voice can actually read aloud. |
| [`stt.py`](stt.py) | [`stt.pyi`](stt.pyi) | `run`, `transcribe` | stt.py — aiwbot's binding of the shared STT: workspace vocabulary primed in (C1, C3, C4). |
| [`tts.py`](tts.py) | [`tts.pyi`](tts.pyi) | `encode_ogg`, `synthesize` | tts.py — TTS wrapper: Kokoro-82M pf_dora voice, lazy-loaded; local OGG/Opus encode (C5, C6). |
<!-- routing:end -->
