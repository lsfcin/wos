# chat
> Exported conversation to navigable text — voice notes transcribed inline, bot noise dropped,
> secrets redacted. Provider leaf: `wazip` (WhatsApp).

The sibling of [`../video/`](../video/CONTEXT.md), one input apart: that one turns a *link* into
text, this one turns a *chat export* into text. The workspace could already read a mailbox and a
video and was deaf to WhatsApp — which is where the obra, the feirinha and the instituto actually
happen, so the facts lived in audio nobody could grep.

**Priming is the caller's, not the tool's.** `--prompt-file` takes writing in the speakers' own
register, and the domain vocabulary has to be *inside the sentences*: a bare word list anywhere in
the prompt suppresses punctuation — measured 0.0 marks per 100 words against 22.5 for the same
jargon dissolved into writing. Without the flag it primes for punctuation only and teaches no words.
A live example is [`code/obra/hotwords_obra.py`](../../../code/obra/hotwords_obra.py), which primes
for cartório and construction terms.

The engine is [`../audio/stt.py`](../audio/CONTEXT.md) — faster-whisper `large-v3-turbo`, local, no
network. An audio the model doubts is written as an explicit "not understood" marker, never as
silence: a spoken turn missing from the record is worse than one marked illegible.

```
core/run tools/chat/wazip <export.zip>... --out <dir> [--prompt-file <carrier.txt>] [--keep-media <dir>]
```

By default the zip stays the archive and only the text is written — the media is what makes these
exports hundreds of megabytes, and it belongs on Drive, not in git.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`chat_stitch.py`](chat_stitch.py) | [`chat_stitch.pyi`](chat_stitch.pyi) | `transcript_for`, `fold`, `is_noise`, `stitch`, `span` | chat_stitch.py — a chat export becomes one readable conversation: every "audio attached" line gains what was actually said underneath, bot menus that repeat verbatim go, and secrets are redacted. |
| [`chat_transcribe.py`](chat_transcribe.py) | [`chat_transcribe.pyi`](chat_transcribe.pyi) | `duration`, `audios`, `sidecar`, `eta`, `run` | chat_transcribe.py — batch speech-to-text over an extracted chat export; one .txt sidecar per audio. Resumable: an audio whose sidecar already exists is skipped, so a killed run loses nothing. |
| [`wazip`](wazip) | — | — | a WhatsApp export becomes navigable text: audios transcribed inline, bot menus dropped, secrets redacted. |
<!-- routing:end -->
