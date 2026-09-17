# select
> The picker keyboards: which grid a tap opens, and what one tap costs.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — marks tests/select as a package. |
| [`test_f3c_tap_latency.py`](test_f3c_tap_latency.py) | [`test_f3c_tap_latency.pyi`](test_f3c_tap_latency.pyi) | `answer`, `edit_message_reply_markup` | test_f3c_tap_latency.py — F3c: a panel tap costs ONE Telegram round trip, not two or three. |
| [`test_panel.py`](test_panel.py) | [`test_panel.pyi`](test_panel.pyi) | `answer`, `edit_message_reply_markup` | test_panel.py — free unit test: panel effects — scopes, applying a choice, hidden dims. |
| [`test_panelmenu.py`](test_panelmenu.py) | [`test_panelmenu.pyi`](test_panelmenu.pyi) | — | test_panelmenu.py — free unit test: panel layout — rows, controls, ordering, paging. |
<!-- routing:end -->
