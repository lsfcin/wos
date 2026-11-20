# SPEC: frontend — audio-in-out voice pipeline
<!-- Machine-parseable module contract (spec-driven development). Keep the header keys below. -->
spec-version: 0 status: locked verify: none

<!-- Scope: the voice surface added by feature/audio-in-out (STT in, TTS out) over the existing
     Telegram frontend. Non-voice files (bot text routing, dispatch, format, inbox, reply text
     paths) keep their prior behavior; this contract governs the new/changed voice boundaries.
     Loop 6 folds the Carry criteria + Loop-3 boundaries here and flips status -> locked. -->

## Inputs
- A Telegram voice note: `voice.file_id: str` reaching `bot._handle_message`.
- `hotwords.HOTWORDS: list[str]` — explicit editable literal (workspace jargon, model names, EN loanwords), no inline strings (C4). It is the **checklist**, not the prompt: every word in it must appear inside some `hotwords.CARRIER` sentence, which `test_as_prompt_joins_every_hotword_into_one_string` enforces. Whisper imitates the style it is primed with, so punctuation has to be *in* the prompt — and **corrected 2026-07-27**: a bare word list ANYWHERE in the prompt suppresses punctuation, not merely at the tail. Measured on Lucas's chuveiro voice note: sentences-then-list 0.0 marks/100 words, list-then-sentences 1.1, jargon dissolved into the sentences 22.5. The prompt is prose end to end.
- On voice-out: the delivered turn text `result.text: str` (plain-stripped via `format.plain`, clipped to a sane cap).
- `stt.run` accepts an injectable `model` (the C1/C3 test boundary); `tts.encode_ogg` accepts a synthetic numpy waveform + `sample_rate: int` (the C5 test boundary).

## Outputs
- `hotwords.as_prompt() -> str` — the CARRIER sentences and nothing else, fed to faster-whisper's `initial_prompt=` (was `hotwords=` before F3b, was `CARRIER + HOTWORDS` until 2026-07-27; signature unchanged throughout, mechanism corrected twice).
- `startword.normalize(text: str) -> str` — a misheard `bote` opener rewritten to `bot`. The voice path echoes and routes the SAME normalized string, so the echo shows what actually reached the session.
- `stt.run(path: Path, model) -> str` and `stt.transcribe(path: Path) -> str` — transcript text; `""` on empty/exception (C1/C3) **or on a transcript the model itself doubts** (F3b).
- `stt.confident(segments) -> bool` — mean `avg_logprob` over the segments vs `_MIN_LOGPROB`.
- `speech.to_speech(markdown: str) -> str` — an agent's markdown answer as prose a voice can read.
- `tts.encode_ogg(samples, sample_rate: int) -> bytes` — OGG/Opus bytes (Opus magic header present);
  `tts.synthesize(text: str) -> bytes` (C5).
- `reply.send_voice(msg, ogg_bytes: bytes) -> Message | None` — best-effort voice reply; `None` on failure (text already delivered).
- Voice-in path yields either a routed turn (`_route_text(..., spoken=True)`) or a transcribed INBOX entry — never an untranscribed dump when text is present (C1).

## Invariants
- Heavy models (`faster_whisper`, `kokoro`) are lazy-imported INSIDE `stt._model()` / `tts._pipeline()`, never at module top: importing `stt`/`tts` must succeed with the deps uninstalled (C6).
- `stt.run` wraps transcription in try/except and returns `""` on ANY failure; empty and exception both collapse to `""` (C3).
- An empty transcript is NEVER dispatched: the voice branch guards on `t.strip()` and on empty falls back to transcribed→untranscribed INBOX + a `TRANSCRIBE_FAIL_PHRASES` notice (C3).
- The `spoken: bool` flag is kw-only with default `False`; text-triggered turns are byte-for-byte unaffected (C5). Voice reply is additive — its failure never blocks the already-delivered text.
- Voice transcripts route through the SAME `_route_text` as typed text (symmetry); the `"bot"` prefix is parsed by the existing `_strip_bot_prefix` (now `startword.strip_prefix`), no new prefix logic (C2).
- The voice reply is fed `speech.to_speech(result.text)`, NEVER `format.plain` — that is `html.escape`, which is the opposite of prose and had Kokoro pronouncing `&#x27;` and table pipes (F3b).
- A low-confidence transcript degrades exactly like an empty one: untranscribed INBOX entry plus a notice. Whisper hallucinates words on near-silent audio and no decoding setting prevents it, so the guard is confidence, not settings — and a false reject is recoverable where a dispatched hallucination costs a real turn.

## Examples
Test coverage: `tests/test_stt.py` (C1 transcription success, C3 empty/exception), `tests/test_tts.py` (C5 OGG/Opus encode), `tests/test_route_text.py` (C2 "bot" prefix via spoken=True), `tests/test_hotwords.py` (C4 editable data), integration verified in `tests/test_reply_voice.py`.

- `stt.run(path, fake_model)` where `fake_model.transcribe` yields segments `["oi", " mundo"]` → `"oi mundo"`.
- `stt.run(path, raising_model)` (transcribe raises) → `""`; `stt.run(path, empty_model)` (no segments) → `""` (C3).
- `tts.encode_ogg(sine_wave_24k, 24000)` → non-empty `bytes` beginning with the OGG magic (`b"OggS"`), no model load (C5).
- Transcript `"bot roda os testes"` through `_route_text(spoken=True)` → `_strip_bot_prefix` → `_cmd_new` starts a new session (C2).
- Hotwords from `hotwords.as_prompt()` — workspace jargon list fed to faster-whisper's `hotwords=` (C4).

## Notes
- Provenance: `.craft/audio-in-out/` (3-arch.md architecture, 3b-contracts.md contracts). Corrected boundary:
  `inbox.save_media` is `async` and its real signature is `save_media(file_id: str, context, suffix: str) ->
  pathlib.Path` — the voice branch must `await inbox.save_media(voice.file_id, context, ".ogg")` before transcription
  (whisper needs the file on disk).
- `soundfile` is a top-level import (C6 installs it); only `faster_whisper`/`kokoro` are lazy.
- Sibling contracts: `dispatch.pyi`, `inbox.pyi`, `format.pyi`, `phrases.pyi` (existing frontend interfaces).
