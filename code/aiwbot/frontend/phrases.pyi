from _typeshed import Incomplete

CAPTURE_ACKS: Incomplete
WORKING_PHRASES: Incomplete
NEW_EMPTY_PROMPT_PHRASES: Incomplete
ERROR_PHRASES: Incomplete
UNKNOWN_CMD_PHRASES: Incomplete
SESSION_LIVE_ELSEWHERE_PHRASES: Incomplete
RESUME_EMPTY_PHRASES: Incomplete
RESUME_ANCHOR_PHRASES: Incomplete
LISTENING_PHRASES: Incomplete
RETRY_PHRASES: Incomplete
TRANSCRIBE_FAIL_PHRASES: Incomplete
ASK_HINT: str
ASK_TAKEN: str
ASK_STALE: str
HELP_TEXT: str

def pick(bank: list[str], **kw) -> str: ...
def pin() -> str: ...
