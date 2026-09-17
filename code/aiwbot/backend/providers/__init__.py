# __init__.py — facade: the concrete backends. Registered in backend/__init__.py, not here.
from .claude import ClaudeBackend
from .opencode import OpencodeBackend

__all__ = ["ClaudeBackend", "OpencodeBackend"]
