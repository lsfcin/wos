from . import answer as answer, landing as landing
from .. import reply as reply
from ..session import Anchors as Anchors
from ..text import markdown as markdown
from .bubbles import Bubbles as Bubbles
from .cadence import Cadence as Cadence
from _typeshed import Incomplete

STREAM_SEAL: bool

class Painter:
    pin: Incomplete
    lead: Incomplete
    clock: Incomplete
    origin: Incomplete
    seal: Incomplete
    anchors: Incomplete
    bubbles: Incomplete
    base: int
    bare_now: list[str]
    text: str
    busy: bool
    frozen: bool
    def __init__(self, working, pin: str, clock=..., origin=None, on_bubble=None, seal: bool = ..., lead: str = '') -> None: ...
    @property
    def sent(self) -> list: ...
    @property
    def answers(self) -> list: ...
    async def note_session(self, session_id: str | None) -> None: ...
    def frames(self, pinned: bool = True) -> list[str]: ...
    async def cut(self) -> None: ...
    def tail_of(self, text: str) -> str: ...
    async def finish(self, block: str, markup=None) -> list: ...
    async def paint(self, delta: str, session_id: str | None = None) -> None: ...
