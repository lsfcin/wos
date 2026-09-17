# voice
> The audio-in-out pipeline: transcribe in, speak out, and what the chat says while it listens.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — marks tests/voice as a package. |
| [`test_f6_voice_feedback.py`](test_f6_voice_feedback.py) | [`test_f6_voice_feedback.pyi`](test_f6_voice_feedback.pyi) | — | test_f6_voice_feedback.py — a voice note says something back before it has been transcribed (Lucas, 2026-07-28: "demora para aparecer qualquer feedback"). The download plus whisper take seconds, and silence for that long reads as being ignored. |
| [`test_hotwords.py`](test_hotwords.py) | [`test_hotwords.pyi`](test_hotwords.pyi) | — | test_hotwords.py — free unit test: hotwords is explicit editable data (C4), not inline in stt.py. |
| [`test_reply_voice.py`](test_reply_voice.py) | [`test_reply_voice.pyi`](test_reply_voice.pyi) | `FakeMsg`, `FailingMsg`, `reply_voice`, `reply_voice` | test_reply_voice.py — free unit test: reply.send_voice (C5), mirrors safe_reply's Telegram-error tolerance so a rejected voice send degrades to None rather than raising. |
| [`test_speech.py`](test_speech.py) | [`test_speech.pyi`](test_speech.pyi) | — | test_speech.py — free unit test: markdown answer -> prose a TTS voice can read (F3b). |
| [`test_stt.py`](test_stt.py) | [`test_stt.pyi`](test_stt.pyi) | `FakeSegment`, `FakeModel`, `transcribe` | test_stt.py — free unit test: STT wrapper (C1 transcription, C3 fail-safe, C6 no live calls). |
| [`test_tts.py`](test_tts.py) | [`test_tts.pyi`](test_tts.pyi) | — | test_tts.py — free unit test: TTS wrapper (C5 voice reply) + local OGG/Opus encode (C6, no live calls). |
| [`test_voice_echo_and_picker.py`](test_voice_echo_and_picker.py) | [`test_voice_echo_and_picker.pyi`](test_voice_echo_and_picker.pyi) | — | test_voice_echo_and_picker.py — Lucas's 2026-07-27 live test: STT conditioning prompt shape, the transcript echo, and a picker that stops reshuffling itself under his thumb. |
<!-- routing:end -->
