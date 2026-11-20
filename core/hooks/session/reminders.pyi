from _typeshed import Incomplete

INBOX: Incomplete
INBOX_WARN: Incomplete
INBOX_LOUD: Incomplete
COMPASS_LOG: Incomplete
COMPASS_STALE_DAYS: int
PUBLISH_WARN: int
DISK_WARN: Incomplete
DISK_LOUD: Incomplete

def read_body(text: str) -> str: ...
def count_entries(body: str) -> int: ...
def inbox() -> str: ...
def compass() -> str: ...
def publish() -> str: ...
def disk() -> str: ...

PR_STATE: Incomplete
PR_EVERY: Incomplete
PR_MARK: str

def prs(now: float | None = None) -> str: ...

ASKS: Incomplete

def main() -> int: ...
