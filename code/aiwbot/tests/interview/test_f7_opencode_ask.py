# test_f7_opencode_ask.py — opencode parity: the ask transport and the retry vocabulary.
#
# Every constant here was measured against opencode 1.18.7 on 2026-07-29 (SPECS AD-31), the way
# AD-27 was measured for claude: `opencode run` has NO MCP flag, the config rides in
# OPENCODE_CONFIG_CONTENT, and the tool call dies at ~60 s unless the per-server `timeout` lifts it.
import json
import pytest
from backend import TurnOptions
from backend.providers import opencode
from backend.providers.claude import ClaudeBackend
from backend.providers.opencode import OpencodeBackend
from frontend.interview import ask, askserver
from frontend.turn import dispatch, helpers

_TOKEN = "abc123"
_PORT = 8787
# The overload text captured live for b2. The outer name stays "UnknownError", so this string is
# the only thing that says what actually happened.
_OVERLOAD = "ResourceExhausted: Worker local total request limit reached (48/48)"


def _options() -> TurnOptions:
    url = askserver.url(_TOKEN, _PORT)
    return TurnOptions(ask_url=url)


def _opencode_config(options: TurnOptions) -> dict:
    env = OpencodeBackend().env(options)
    return json.loads(env["OPENCODE_CONFIG_CONTENT"])


def _server_entry(options: TurnOptions) -> dict:
    config = _opencode_config(options)
    servers = config["mcp"]
    return servers[askserver.SERVER_NAME]


def test_the_ask_url_becomes_each_clis_own_config():
    """One URL in, two providers' real shapes out. The boundary carries the URL and nothing else,
    because "the JSON its CLI's config flag takes" was only provider-agnostic while claude was the
    single provider: opencode's config is a different shape AND arrives by a different road."""
    options = _options()
    url = options.ask_url

    args = ClaudeBackend().build_args("oi", None, options)
    payload = json.loads(args[args.index("--mcp-config") + 1])
    servers = payload["mcpServers"]
    assert servers[askserver.SERVER_NAME]["url"] == url
    assert "--strict-mcp-config" in args, "other MCP servers must not leak into a bot turn"

    entry = _server_entry(options)
    assert entry["url"] == url
    assert entry["type"] == "remote"

    oc_args = OpencodeBackend().build_args("oi", None, options)
    flags = [arg for arg in oc_args if "mcp" in arg]
    assert flags == [], "measured: `opencode run` has no MCP flag, so nothing may reach the argv"


def test_a_turn_that_may_not_ask_is_invoked_exactly_as_before():
    """The same rollback shape as claude's: no ask means no config at all, never an empty one —
    an env var naming a server the daemon is not hosting would cost every turn a failed connect."""
    env = OpencodeBackend().env(TurnOptions())
    assert "OPENCODE_CONFIG_CONTENT" not in env
    assert OpencodeBackend().supports_ask(TurnOptions()) is True, "opencode can host the ask tool"


def test_the_opencode_tool_call_outlives_the_wait_the_bot_promises():
    """Measured: opencode cancels the call at ~60 s (62 s observed) and the agent then answers "a
    ferramenta retornou timeout" — the turn ends on an apology instead of on a question. NO env var
    lifts it (MCP_TOOL_TIMEOUT is claude's alone); the per-server `timeout` does. So the bot's own
    wait must still be the one that ends first, bought here with config rather than with env."""
    entry = _server_entry(_options())
    budget = entry["timeout"]
    assert budget > ask.WAIT_SECONDS * 1000, "the CLI would time out before Lucas could answer"


def test_opencodes_own_overload_text_is_retried_like_a_529():
    """Its overload wording shares no marker with claude's, so before this the retry was
    claude-only in practice: the same failure that a claude turn survives killed an opencode one."""
    overloaded = dispatch.DispatchError(_OVERLOAD)
    assert helpers.transient(overloaded) is True
    request_fault = dispatch.DispatchError("no conversation found")
    assert helpers.transient(request_fault) is False, "a bad request fails the same every time"


def test_an_overloaded_opencode_turn_reaches_the_retry_as_that_text():
    """The whole claim, end to end and free: an `error` line becomes the DispatchError message that
    `transient` reads. Asserting the marker alone would pass even if the text never got there."""
    error = {"name": "UnknownError", "data": {"message": _OVERLOAD}}
    line = json.dumps({"type": "error", "sessionID": "ses_1", "error": error})
    events = opencode.parse_events(line)
    with pytest.raises(dispatch.DispatchError) as raised:
        dispatch.events_to_result(events)
    assert helpers.transient(raised.value) is True
