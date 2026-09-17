from . import ask as ask
from _typeshed import Incomplete
from backend import ASK_SERVER_NAME

PROTOCOL: str
SERVER_NAME = ASK_SERVER_NAME
TOOL_NAME: str
HOST: str
DEFAULT_PORT: int
TOOL: Incomplete

def url(token: str, at_port: int) -> str: ...
def port() -> int: ...
async def handle_rpc(token: str, body: dict) -> dict | None: ...
async def start(at_port: int = ...) -> int: ...
