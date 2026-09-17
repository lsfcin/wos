# sessions.py — cross-backend session listing: the /resume picker aggregates each backend's own
# store so it sees VSCode sessions too, not just ours. Bot-owned state lives in registry.py.
from __future__ import annotations
from backend import get_backend, backend_names
from . import registry


def _title_matches(title: str | None, query: str) -> bool:
    lowered = (title or "").lower()
    return (not query) or (query in lowered)


def _all(cwd: str) -> list[dict]:
    """Every resumable session for cwd, aggregated across backends, each tagged with its backend."""
    items: list[dict] = []
    for name in backend_names():
        backend = get_backend(name)
        listed = backend.list_sessions(cwd)
        for item in listed:
            item["backend"] = name
            items.append(item)
    items.sort(key=lambda e: e["updated_at"], reverse=True)
    return items


def _fill(item: dict, cwd: str) -> None:
    """Complete one page entry. `session_detail` is the per-session query some stores need
    (opencode) and others already answered while listing (claude), so asking here makes the
    cost scale with the page shown rather than with every session that exists."""
    sid = item["session_id"]
    backend = get_backend(item["backend"])
    detail = backend.session_detail(sid, cwd)
    for key, value in detail.items():
        item[key] = value
    item.setdefault("preview", None)
    # The store's mode is what an outside session last ran in; the registry's is what the NEXT
    # turn will use — so a sticky value wins and the store's is the fallback.
    stored = item.get("mode") or registry.DEFAULT_MODE
    item["mode"] = registry.mode_for(sid, stored)
    if not item.get("context_window"):
        window = registry.context_window_for(item.get("model"))
        item["context_window"] = window


def recent(n: int, query: str, cwd: str, offset: int = 0) -> list[dict]:
    """Newest-first sessions (optionally title-filtered) for the /resume picker, from the backend
    stores. Adopts each shown session into the registry so a later tap can resolve backend+title.
    offset paginates: the picker shows one page at a time behind ‹ / › buttons."""
    q = query.lower()
    items = []
    for item in _all(cwd):
        if _title_matches(item.get("title"), q):
            items.append(item)
    page = items[offset:offset + n]
    for item in page:
        registry.adopt(item["session_id"], item["backend"], item.get("title"), item["updated_at"])
        _fill(item, cwd)
    return page


def count(query: str, cwd: str) -> int:
    q = query.lower()
    total = 0
    for item in _all(cwd):
        if _title_matches(item.get("title"), q):
            total += 1
    return total


def last_response(session_id: str, cwd: str) -> str:
    """Full text of the session's last answer, from whichever backend owns it."""
    name = registry.backend_for(session_id)
    text = ""
    if name:
        backend = get_backend(name)
        text = backend.last_response(session_id, cwd)
    return text
