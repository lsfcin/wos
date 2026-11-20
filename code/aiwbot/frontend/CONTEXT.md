# frontend
> Telegram frontend on the AgentBackend boundary — /new + reply-to-continue + INBOX capture.
> spec: SPECS.md

## Shape — the root is the bot itself, every subdirectory is one surface

Split 2026-08-01 at 38 files in one flat directory, where `stt.py` sat beside `msgmap.py` beside `table.py` and nothing but the filename said which was which. Only five things stay at the root: the PTB wiring (`bot`), the config file (`config`), the Telegram send primitives (`reply`), the phrase banks (`phrases`), and the $0 INBOX capture (`inbox`) — each used by every surface below and owned by none of them.

The routing table names the surfaces. Two are worth telling apart before you route: `stream/` is the answer *arriving* (which bubbles are open, when they may move), `text/` is what any of it *looks like* (markdown → Telegram HTML) and knows nothing about messages. `turn/` runs one message end to end and is the only surface that talks to a backend.

Two modules were renamed on the way in, because `turn.turnrun` says the same word twice:
`turnrun` → [`turn/runner.py`](turn/runner.py), `turnhelpers` → [`turn/helpers.py`](turn/helpers.py).

Each subdirectory carries its own `CONTEXT.md`, without which the routing generator folds it back into this table and the split buys the reader nothing: this table went 38 rows → 12. Each also re-declares `> spec: ../SPECS.md`, because the spec gate stops at the nearest ancestor that declares one — a subdirectory saying `spec: none` would have quietly unlocked it.

Tests mirror these names one for one under [`tests/`](../tests/CONTEXT.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`interview/`](interview/CONTEXT.md) | The agent asking Lucas a question mid-turn: the broker, its transport, and the bubble it draws. |
| [`select/`](select/CONTEXT.md) | The picker keyboards: what a scope may be offered, drawn as rows of buttons. |
| [`session/`](session/CONTEXT.md) | Which session a message belongs to, and everything the bot remembers about it. |
| [`stream/`](stream/CONTEXT.md) | The answer arriving live: which bubbles are open, when they may move, and how they land. |
| [`text/`](text/CONTEXT.md) | Agent markdown becomes Telegram HTML: blocks, inline spans, tables, and chunks that never break a tag. |
| [`turn/`](turn/CONTEXT.md) | One message in, one answer out: read the intent, run the backend, put the answer on screen. |
| [`voice/`](voice/CONTEXT.md) | The audio-in-out pipeline: what the bot hears, and what it says back. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: Telegram frontend on the AgentBackend boundary. Import frontend only through here. |
| [`SPECS.md`](SPECS.md) | — | — | SPEC: frontend — audio-in-out voice pipeline |
| [`bot.py`](bot.py) | [`bot.pyi`](bot.pyi) | `main` | bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX. |
| [`config.py`](config.py) | [`config.pyi`](config.pyi) | `config_dir`, `load_config`, `save_config`, `bot_token`, `allowed_chat_id` | config.py — aiwbot's own Telegram config dir (separate token/storage from the old workspace bot). |
| [`inbox.py`](inbox.py) | [`inbox.pyi`](inbox.pyi) | `CaptureLost`, `append_entry`, `build_entry`, `save_media` | inbox.py — capture plain text/media into brain/INBOX.md ($0, no backend call). |
| [`phrases.py`](phrases.py) | [`phrases.pyi`](phrases.pyi) | `pick`, `pin` | phrases.py — phrase banks (natural-language variants, picked at random per message) + help text. |
| [`reply.py`](reply.py) | [`reply.pyi`](reply.pyi) | `safe_reply`, `send_typing`, `edit_text`, `send_voice`, `drop` | reply.py — Telegram send primitives: safe reply, chunking, edit-in-place delivery. |
<!-- routing:end -->
