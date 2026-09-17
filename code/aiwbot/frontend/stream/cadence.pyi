from _typeshed import Incomplete

MIN_INTERVAL: float
BUBBLE_GAP: float
TYPING_EVERY: float
MIN_GROWTH: int
MAX_INTERVAL: float

class Cadence:
    clock: Incomplete
    interval: Incomplete
    last_at: float
    typing_at: float
    born_at: Incomplete
    painted: int
    def __init__(self, clock=...) -> None: ...
    def due(self, size: int) -> bool: ...
    def spaced(self) -> bool: ...
    def typing_due(self) -> bool: ...
    def mark_paint(self, size: int, ok: bool) -> None: ...
    def mark_bubble(self) -> None: ...
