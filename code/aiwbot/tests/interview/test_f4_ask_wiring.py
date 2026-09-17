# test_f4_ask_wiring.py — F4 Stage 4: the transport and the CLI wiring around the broker.
#
# Every constant asserted here was measured against the real binary on 2026-07-27 rather than
# read off documentation: `claude -p` re-runs `initialize` several times per invocation, kills a
# tool call at 60 s unless MCP_TOOL_TIMEOUT lifts it, and refuses MCP tools outright in plan mode.
import asyncio
import json
from backend import TurnOptions
from backend.providers.claude import ClaudeBackend
from backend.cli import CliBackend
from frontend.interview import ask, askserver

_TOKEN = "abc123"


def _rpc(method: str, params: dict | None = None, token: str = _TOKEN) -> dict | None:
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    return asyncio.run(askserver.handle_rpc(token, body))


def test_the_tool_is_listed_with_the_question_it_needs():
    listed = _rpc("tools/list")
    tools = listed["result"]["tools"]
    assert [t["name"] for t in tools] == [askserver.TOOL_NAME]
    schema = tools[0]["inputSchema"]
    assert schema["required"] == ["question"]
    assert "options" in schema["properties"]


def test_the_handshake_is_idempotent_because_the_cli_repeats_it():
    """Measured: one `claude -p` run sends `initialize` three times. A server that allocated
    per-connection state on it would answer the second from a half-built session, so the
    handshake must be a pure function of the request."""
    params = {"protocolVersion": askserver.PROTOCOL}
    first = _rpc("initialize", params)
    second = _rpc("initialize", params)
    assert first == second
    assert first["result"]["serverInfo"]["name"]
    assert first["result"]["capabilities"]["tools"] is not None


def test_a_notification_is_answered_with_nothing_at_all():
    """`notifications/initialized` carries no id, and a JSON-RPC response to a notification is
    a protocol error — so the transport has to be able to say "no body" (HTTP 202)."""
    assert _rpc("notifications/initialized") is None


def test_an_unknown_method_is_a_protocol_error_not_a_crash():
    response = _rpc("resources/list")
    assert response["error"]["code"] == -32601


def test_the_cli_is_pointed_at_the_daemons_own_server_only_when_one_is_listening():
    backend = ClaudeBackend()
    plain = backend.build_args("oi", None, TurnOptions())
    assert "--mcp-config" not in plain

    at = askserver.url(_TOKEN, 8787)
    args = backend.build_args("oi", None, TurnOptions(ask_url=at))
    assert "--strict-mcp-config" in args, "other MCP servers must not leak into a bot turn"
    payload = json.loads(args[args.index("--mcp-config") + 1])
    url = payload["mcpServers"][askserver.SERVER_NAME]["url"]
    assert url.endswith(f"/mcp/{_TOKEN}")
    assert "127.0.0.1" in url, "the broker listens on loopback only"


def test_the_prompt_stays_last_on_the_argv():
    """`claude -p … <prompt>` takes the prompt positionally: measured, a flag appended after it
    makes the CLI exit with "Input must be provided either through stdin or as a prompt"."""
    at = askserver.url(_TOKEN, 8787)
    args = ClaudeBackend().build_args("faz isso", "s1", TurnOptions(ask_url=at))
    assert args[-1] == "faz isso"


def test_plan_mode_does_not_offer_ask_because_the_cli_refuses_it():
    """Measured: `claude -p --permission-mode plan` answers an MCP tool call with "Cannot call
    mcp__aiwbot__ask_user while in plan mode", and an explicit --allowedTools does not lift it.
    Offering the tool there would spend a turn on a call that cannot land."""
    backend = ClaudeBackend()
    assert backend.supports_ask(TurnOptions(mode="build")) is True
    assert backend.supports_ask(TurnOptions(mode="plan")) is False
    assert CliBackend().supports_ask(TurnOptions()) is False, "opt-in, never assumed"


def test_the_tool_can_be_taken_away_from_the_phone(store, monkeypatch):
    """Same rollback shape as streaming: one line in config.json plus a restart. A turn that may
    not ask is invoked exactly as it was before Stage 4 — no MCP flags at all."""
    monkeypatch.setattr(askserver, "port", lambda: 8787)
    from frontend.session import registry
    from frontend.turn import helpers
    registry.set_setting("s1", "backend", "claude")

    allowed = TurnOptions(mode="build")
    assert helpers.enable_ask("s1", "claude", allowed) is not None
    assert allowed.ask_url

    registry.set_setting("s1", "ask", "false")
    refused = TurnOptions(mode="build")
    assert helpers.enable_ask("s1", "claude", refused) is None
    assert refused.ask_url is None


def test_the_cli_tool_timeout_outlives_the_wait_the_bot_promises():
    """The CLI kills a tool call at 60 s by default — far under the hour Lucas asked to have to
    answer. The env var lifts it, and the bot's own wait must end FIRST, so an unanswered
    question comes back as the bot's text and never as the CLI's timeout."""
    env = ClaudeBackend().env(TurnOptions())
    budget = int(env["MCP_TOOL_TIMEOUT"])
    assert budget > ask.WAIT_SECONDS * 1000
    assert ask.WAIT_SECONDS >= 45 * 60, "Lucas asked for about an hour to answer"
