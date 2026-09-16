from _typeshed import Incomplete
from pathlib import Path
from typing import Any

def emit_allow(message: str = '') -> None: ...

DISPATCH: Incomplete

def gate(payload: dict[str, Any], tool: str, root: Path, messages: list[str]) -> bool: ...
def main() -> int: ...
