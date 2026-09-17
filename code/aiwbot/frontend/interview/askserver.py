# askserver.py — the daemon's own MCP server: one HTTP endpoint per live turn, JSON-RPC by hand.
#
# linuz90's ask_user works because the SDK runs the agent IN-process; aiwbot drives a subprocess
# CLI, so a stdio MCP server would be a child of that CLI and could never reach the bot's Telegram
# state. Hosting the server here inverts it: the CLI is pointed at the daemon over loopback, and
# the tool handler runs where the chat already lives. Plain JSON-RPC over aiohttp — the `mcp` SDK
# would be a new dependency for the ~40 lines below (measured against the real CLI, 2026-07-27).
from __future__ import annotations
from aiohttp import web
from backend import ASK_SERVER_NAME
from . import ask

# What the CLI negotiated in the check. Echoed back rather than dictated: the client sends the
# version it wants, and it re-sends `initialize` several times per invocation.
PROTOCOL = "2025-06-18"
# The name is the boundary's, not this server's: every backend writes it into its own config (AD-31).
SERVER_NAME = ASK_SERVER_NAME
TOOL_NAME = "ask_user"
# Loopback only. The turn token in the path is what tells two concurrent turns apart — an MCP
# request carries no turn id of its own, so correlation cannot come from the payload.
HOST = "127.0.0.1"
DEFAULT_PORT = 8787
_PATH = "/mcp/{token}"
_UNKNOWN_METHOD = -32601

TOOL = {
    "name": TOOL_NAME,
    # The first live interview (2026-07-28) came back as six free-text questions: the model read
    # `options` as optional and skipped it, which is the worst answer on a phone. So the default
    # is stated as the rule and free text as the exception.
    "description": ("Pergunta algo ao usuário no Telegram e ESPERA a resposta dele. Use quando a "
                    "decisão é dele (escolha de rumo, ambiguidade real, confirmação antes de algo "
                    "custoso), nunca para narrar progresso. SEMPRE mande `options` com 2 a 4 "
                    "alternativas curtas quando a pergunta admitir alternativas — elas viram "
                    "botões, e um toque é muito mais barato que digitar no celular. Deixe sem "
                    "`options` só quando a resposta for genuinamente aberta. O usuário pode "
                    "responder em texto livre de qualquer forma."),
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "A pergunta, curta e direta."},
            "options": {"type": "array", "items": {"type": "string"},
                        "description": ("Escolhas prontas, se houver. Cada uma vira um botão, "
                                        "então mantenha CURTAS — até ~25 caracteres. Rótulo "
                                        "longo é cortado no celular; o detalhe vai na pergunta, "
                                        "não no botão.")},
        },
        "required": ["question"],
    },
}

_runner = None
_port = 0


def url(token: str, at_port: int) -> str:
    """Where one turn reaches this server: its own path, on loopback. This is all the boundary carries —
    the config that names it is per-provider, in shape AND in road, so it belongs to each backend
    (AD-31: claude takes JSON on the argv, opencode takes it in the environment)."""
    return f"http://{HOST}:{at_port}/mcp/{token}"


def port() -> int:
    """The port the server is listening on, or 0 when it never came up — which is what makes
    ask degrade silently instead of breaking every turn."""
    return _port


def _ok(rpc_id, payload: dict) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "result": payload}


def _handshake(body: dict) -> dict:
    params = body.get("params") or {}
    version = params.get("protocolVersion") or PROTOCOL
    return {"protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": "1"}}


async def _call(token: str, params: dict) -> dict:
    """Run the one tool this server has. Its answer is CONTENT even when nobody answered: an MCP
    error would abort the agent's turn, and the wait ending is not a failure of the turn."""
    arguments = params.get("arguments") or {}
    question = arguments.get("question") or ""
    options = arguments.get("options") or []
    text = await ask.ask(token, question, options)
    return {"content": [{"type": "text", "text": text}]}


async def handle_rpc(token: str, body: dict) -> dict | None:
    """One JSON-RPC request for one turn. `None` means "notification": no response at all, which
    the HTTP layer turns into a 202. Every branch is a pure function of the request, because the
    CLI repeats `initialize` and a server holding per-connection state would answer the repeats
    from a half-built session."""
    method = body.get("method") or ""
    rpc_id = body.get("id")
    response: dict | None = None
    if method.startswith("notifications/"):
        response = None
    elif method == "initialize":
        response = _ok(rpc_id, _handshake(body))
    elif method == "tools/list":
        response = _ok(rpc_id, {"tools": [TOOL]})
    elif method == "tools/call":
        payload = await _call(token, body.get("params") or {})
        response = _ok(rpc_id, payload)
    else:
        error = {"code": _UNKNOWN_METHOD, "message": f"unknown method: {method}"}
        response = {"jsonrpc": "2.0", "id": rpc_id, "error": error}
    return response


async def _handle(request):
    token = request.match_info["token"]
    body = await request.json()
    answered = await handle_rpc(token, body)
    if answered is None:
        result = web.Response(status=202)
    else:
        result = web.json_response(answered)
    return result


async def start(at_port: int = DEFAULT_PORT) -> int:
    """Bring the server up inside the bot's own event loop, once. Returns the live port, or 0 if
    it could not bind — the daemon must still run without ask rather than fail to start."""
    global _runner, _port
    if _runner is None:
        app = web.Application()
        app.router.add_post(_PATH, _handle)
        runner = web.AppRunner(app)
        await runner.setup()
        try:
            site = web.TCPSite(runner, HOST, at_port)
            await site.start()
            _runner, _port = runner, at_port
        except OSError as e:
            print(f"ask server did not start on {HOST}:{at_port} ({e}) — ask_user disabled")
    return _port
