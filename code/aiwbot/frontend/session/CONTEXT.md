# session
> Which session a message belongs to, and everything the bot remembers about it.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: which session a message belongs to. Import session only through here. |
| [`anchor.py`](anchor.py) | [`anchor.pyi`](anchor.pyi) | `Anchors`, `note_session`, `add` | anchor.py — map each answer bubble to its session, so any of them can be replied to (AD-23). |
| [`msgmap.py`](msgmap.py) | [`msgmap.pyi`](msgmap.pyi) | `remember_reply`, `session_for_reply`, `remember_pending_new`, `pending_new`, `remember_ask` | msgmap.py — bounded message_id -> value maps: which session, which scope, which panel state. A Telegram message is the only handle a callback carries, so everything the bot needs to know about a keyboard is keyed by the message it sits on — that is what keeps callback_data free. |
| [`registry.py`](registry.py) | [`registry.pyi`](registry.pyi) | `remember`, `adopt`, `defaults`, `setting_for`, `set_setting` | registry.py — bot-owned per-session state in config.json: knobs, titles, message maps. Side-state only: the provider stores stay the source of truth for what sessions exist (AD-6). |
| [`resume.py`](resume.py) | [`resume.pyi`](resume.pyi) | `cmd_resume`, `handle_callback` | resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue. |
| [`sessions.py`](sessions.py) | [`sessions.pyi`](sessions.pyi) | `recent`, `count`, `last_response` | sessions.py — cross-backend session listing: the /resume picker aggregates each backend's own store so it sees VSCode sessions too, not just ours. Bot-owned state lives in registry.py. |
<!-- routing:end -->
