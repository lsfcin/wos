from .. import phrases as phrases, reply as reply
from ..select import keyboard as keyboard
from ..text import format as format

TAP: str
NO_ANSWER_NOTE: str
TIMEOUT_TEXT: str
ENDED_TEXT: str
EXPIRED_TEXT: str

def markup(question_id: str, options: list[str]): ...
def bubble_text(question: str, options: list[str]) -> str: ...
def answer_note(answered: str) -> str: ...
async def close(bubble, sent: str, answered: str) -> None: ...
