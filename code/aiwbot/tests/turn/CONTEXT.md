# turn
> One message in, one answer out: triggers, directives, delivery, and INBOX capture.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — marks tests/turn as a package. |
| [`test_bot.py`](test_bot.py) | [`test_bot.pyi`](test_bot.pyi) | — | test_bot.py — free unit test: "bot"-prefix trigger routing logic. |
| [`test_directives.py`](test_directives.py) | [`test_directives.pyi`](test_directives.pyi) | — | test_directives.py — F3a: read leading harness/model words off a bot-prefixed message, $0. The index is fixed here so the test neither shells opencode nor reads its sqlite — it pins the PARSING, and backend_names() (used for harness self-aliases) is pure, no I/O. |
| [`test_f2_papercuts.py`](test_f2_papercuts.py) | [`test_f2_papercuts.pyi`](test_f2_papercuts.pyi) | — | test_f2_papercuts.py — the F2 batch: phrase tone, flat glyphs, the reply anchor, and the "bote" mishearing. Each choice below was made by Lucas against a live Telegram prototype (2026-07-26), so these tests pin decisions, not guesses. |
| [`test_inbox.py`](test_inbox.py) | [`test_inbox.pyi`](test_inbox.pyi) | — | test_inbox.py — free unit test: build_entry tags forwarded (non-Lucas) captures. |
| [`test_route_text.py`](test_route_text.py) | [`test_route_text.pyi`](test_route_text.pyi) | `testrun_and_deliver_spoken_sends_voice_in_addition_to_text`, `testrun_and_deliver_not_spoken_never_sends_voice` | test_route_text.py — free unit test: shared text/voice routing (_route_text), the C3 empty-transcript guard, and the C5 spoken-flag threading into run_and_deliver. |
<!-- routing:end -->
