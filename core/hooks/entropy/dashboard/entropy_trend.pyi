from datetime import date
from pathlib import Path

WINDOW_DAYS: int

def baseline(root: Path, window_days: int = ...) -> tuple | None: ...
def format_trend(current: int, base: tuple | None, today: date = None) -> str: ...
