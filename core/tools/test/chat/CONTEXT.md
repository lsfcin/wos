# chat
> T1 coverage for the chat tool: what an audio line must keep, what noise must go, and what must
> never reach a versioned file.

The three questions are separate on purpose. **Keeping** — an audio with no transcript still keeps
its line, because a spoken turn missing from the record is worse than one marked illegible.
**Dropping** — the cartório's chatbot re-sends the same menu on every message, and four copies bury
the two lines a human typed. **Redacting** — a Brazilian mobile with area code is eleven digits and
so is a CPF, so bare digits are only a CPF near a line that says so; that boundary is the reason
this file exists rather than a regex nobody re-reads.

The priming vocabulary is NOT tested here: it is domain data, and its test lives with the domain
that owns it (`code/obra/tests/test_hotwords.py`).

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_chat_stitch.py`](test_chat_stitch.py) | [`test_chat_stitch.pyi`](test_chat_stitch.pyi) | T1 chat stitching: an audio line must never lose what was said, a bot menu must never survive, and a secret must never reach a versioned file. Zero-token, no network, no model. |
<!-- routing:end -->
