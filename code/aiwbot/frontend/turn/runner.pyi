from . import dispatch as dispatch, helpers as helpers
from .. import config as config, phrases as phrases, reply as reply
from ..interview import ask as ask
from ..select import panelmenu as panelmenu
from ..session import msgmap as msgmap, registry as registry
from ..stream import answer as answer, painter as painter
from ..text import format as format
from ..voice import speech as speech, tts as tts
from _typeshed import Incomplete

WORKSPACE_DIR: Incomplete
SPOKEN_CHARS: int
RETRIES: int
RETRY_BACKOFF: float

async def guarded(coro, msg) -> None: ...
async def run_and_deliver(msg, working, prompt: str, *, session_id: str | None, backend_name: str, title: str | None, scope: str, spoken: bool = False, lead: str = '') -> None: ...
async def start_new(msg, prompt: str, *, spoken: bool = False, working=None) -> None: ...
async def handle_reply_continue(msg, sid: str, text: str, *, spoken: bool = False, working=None) -> None: ...
