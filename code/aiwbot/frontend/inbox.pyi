import pathlib
from .config import WORKSPACE_ROOT as WORKSPACE_ROOT
from _typeshed import Incomplete
from telegram.ext import ContextTypes as ContextTypes

BRAIN_ATTACHMENTS: Incomplete
INBOX_FILE: Incomplete
INBOX_MARKER: str

def append_entry(entry: str) -> None: ...
def build_entry(body: str, attachment_path: pathlib.Path | None, *, forwarded: bool = False) -> str: ...
async def save_media(file_id: str, context: ContextTypes.DEFAULT_TYPE, suffix: str) -> pathlib.Path: ...
