# __init__.py — facade: Telegram frontend on the AgentBackend boundary. Import frontend only through here.
from .bot import main

__all__ = ["main"]
