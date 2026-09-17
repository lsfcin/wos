# stream
> The answer arriving live: which bubbles are open, when they may move, and how they land.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: the answer arriving live: which bubbles are open, when they may move, and how they land. |
| [`answer.py`](answer.py) | [`answer.pyi`](answer.pyi) | `quote`, `decorate`, `room`, `bare_frames`, `frames` | answer.py — the shape of one answer message: the agent's text, then the footer that names it. |
| [`bubbles.py`](bubbles.py) | [`bubbles.pyi`](bubbles.pyi) | `Bubbles`, `write`, `open`, `cut`, `discard` | bubbles.py — the messages one answer is written into: which are live, which are sealed, and what each currently holds. Split out of painter.py (2026-07-29) when a question interrupting a turn made "the bubbles of this answer" a structure rather than a list: painter owns WHAT to write, this owns WHERE it went. |
| [`cadence.py`](cadence.py) | [`cadence.pyi`](cadence.pyi) | `Cadence`, `due`, `spaced`, `typing_due`, `mark_paint` | cadence.py — when a streamed answer is allowed to move: repaint rate, typing, bubble spacing. Split out of painter.py when the inter-bubble pause arrived (2026-07-28) and the file hit its size gate: painting owns BUBBLES, this owns TIME. Pure state machine, no I/O and no Telegram — so every rule below is asserted against a fake clock rather than waited for. |
| [`landing.py`](landing.py) | [`landing.pyi`](landing.pyi) | `land`, `stamp` | landing.py — turn the live bubbles into the finished answer: the footer, the keyboard, and the |
| [`painter.py`](painter.py) | [`painter.pyi`](painter.pyi) | `Painter`, `sent`, `answers`, `note_session`, `frames` | painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn. |
<!-- routing:end -->
