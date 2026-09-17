# __init__.py — facade: boundary types + backend registry. Import backends only through here.
from .base import ASK_SERVER_NAME, AgentEvent, AgentBackend, EventKind, TurnOptions
from .caps import Capabilities
from .providers import ClaudeBackend, OpencodeBackend

_BACKENDS = {"claude": ClaudeBackend, "opencode": OpencodeBackend}


def get_backend(name: str) -> AgentBackend:
    factory = _BACKENDS.get(name)
    if factory is None:
        raise ValueError(f"unknown backend: {name}")
    instance = factory()
    return instance


def backend_names() -> list[str]:
    """Registered backend names — the set the session picker aggregates across."""
    return list(_BACKENDS)


__all__ = ["ASK_SERVER_NAME", "AgentEvent", "AgentBackend", "Capabilities", "EventKind",
           "TurnOptions", "get_backend", "backend_names"]
