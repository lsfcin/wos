from . import config as config, inbox as inbox, phrases as phrases, reply as reply
from .interview import ask as ask, askserver as askserver
from .select import choices as choices, panel as panel, panelmenu as panelmenu
from .session import msgmap as msgmap, registry as registry, resume as resume
from .text import format as format
from .turn import helpers as helpers, runner as runner, startword as startword
from .voice import stt as stt
from _typeshed import Incomplete
from telegram import Update as Update
from telegram.ext import ContextTypes as ContextTypes

WORKSPACE_DIR: Incomplete

def main() -> None: ...
