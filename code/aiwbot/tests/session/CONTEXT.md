# session
> Which session a message belongs to, and everything the bot remembers about it.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — marks tests/session as a package. |
| [`test_registry.py`](test_registry.py) | [`test_registry.pyi`](test_registry.pyi) | `store` | test_registry.py — free unit test: scopes (session vs NEW), last-used defaults, message maps. |
| [`test_resume.py`](test_resume.py) | [`test_resume.pyi`](test_resume.pyi) | — | test_resume.py — free unit test: /resume picker list/label/pagination assembly. |
| [`test_sessions.py`](test_sessions.py) | [`test_sessions.pyi`](test_sessions.pyi) | `two_backends`, `list_sessions`, `session_detail` | test_sessions.py — free unit test: cross-backend /resume aggregation + registry adopt/mode. |
<!-- routing:end -->
