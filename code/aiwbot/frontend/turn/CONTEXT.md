# turn
> One message in, one answer out: read the intent, run the backend, put the answer on screen.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: one message in, one answer out: read the intent, run the backend, put the answer on screen. |
| [`directives.py`](directives.py) | [`directives.pyi`](directives.pyi) | `resolve` | directives.py — read leading harness/model words off a bot-prefixed message, no inference. |
| [`dispatch.py`](dispatch.py) | [`dispatch.pyi`](dispatch.pyi) | `TurnResult`, `DispatchError`, `join_texts`, `events_to_result`, `turn` | dispatch.py — one call site that drains any AgentBackend.send() into a single reply. |
| [`helpers.py`](helpers.py) | [`helpers.pyi`](helpers.pyi) | `friendly_error`, `transient`, `parse_new_arg`, `apply_directives`, `turn_options` | helpers.py — turn plumbing: friendly errors, /new arg parsing, sticky options, persistence. Extracted out of bot.py (size gate) — pure helpers with no test-visible monkeypatch boundary. |
| [`runner.py`](runner.py) | [`runner.pyi`](runner.pyi) | `guarded`, `run_and_deliver`, `start_new`, `handle_reply_continue` | runner.py — run one turn and put its answer on screen: dispatch, deliver, anchor, speak. |
| [`startword.py`](startword.py) | [`startword.pyi`](startword.pyi) | `normalize`, `strip_prefix` | startword.py — does a message open with the "bot" session-start word, and what follows it. |
<!-- routing:end -->
