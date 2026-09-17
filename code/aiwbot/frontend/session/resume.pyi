from . import msgmap as msgmap, registry as registry, sessions as sessions
from .. import config as config, phrases as phrases, reply as reply
from ..select import panelmenu as panelmenu
from ..text import format as format

RESUME_COUNT: int
TITLE_WORDS: int
QUERY_MAX: int
RULER_WIDTH: int

async def cmd_resume(msg, arg: str, cwd: str) -> None: ...
async def handle_callback(update, context) -> None: ...
