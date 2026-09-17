# claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object).
from __future__ import annotations
import json
import pathlib
from .. import binaries
from . import transcript
from ..base import ASK_SERVER_NAME, AgentEvent, TurnOptions, add_flag, try_json
# Parsing lives in claudeparse (F4: this file was 194/200 and a stream parser does not
# fit). Re-exported so `from backend.claude import parse_events` keeps working.
from .claudeparse import StreamParser, parse_events  # noqa: F401
from ..caps import Capabilities
from ..cli import CliBackend

_PROJECTS = ".claude/projects"
# The one entrypoint value the native picker lists. "cli" is rejected (falls back to sdk-cli).
_ENTRYPOINT = "claude-vscode"
_MODES = ("build", "plan")
# `--model` takes an alias for the latest model of a family, or a full id. Aliases age better
# than ids, so the picker offers those; a full id still works if it is ever set by hand.
_MODELS = ("sonnet", "opus", "fable")
# One ladder for every claude model — verified in `claude --help` 2026-07-23.
_EFFORTS = ("low", "medium", "high", "xhigh", "max")
# Measured 2026-07-27: the CLI aborts an MCP tool call after ~60 s ("Tool timed out. No answer
# got."), which is nothing next to the hour Lucas wants to answer a question in. This env var
# lifts the ceiling; the bot's own wait still ends first, so the timeout path stays ours and the
# agent gets text back instead of a dead tool call.
_TOOL_TIMEOUT_MS = 3_600_000


def _project_dir(cwd: str) -> pathlib.Path:
    """Claude Code stores a cwd's transcripts under ~/.claude/projects/<cwd, / -> ->."""
    name = cwd.replace("/", "-")
    return pathlib.Path.home() / _PROJECTS / name


def _opening_prompt(path: pathlib.Path) -> str:
    """First `last-prompt` line = the session's opening prompt (near the top -> cheap scan)."""
    title = ""
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            if '"type":"last-prompt"' not in line:
                continue
            obj = try_json(line.strip())
            if obj is not None:
                title = obj.get("lastPrompt") or ""
            break
    return title


def _session_item(path: pathlib.Path) -> dict:
    sid = path.stem
    lines = transcript.tail_lines(path)
    title = transcript.latest_ai_title(lines)
    if not title:
        title = _opening_prompt(path)
    preview = transcript.last_response_text(lines)
    model = transcript.last_model(lines)
    used = transcript.last_context_used(lines)
    updated = path.stat().st_mtime
    return {"session_id": sid, "title": title, "updated_at": updated,
            "preview": preview, "model": model, "context_used": used}


def _mcp_config(ask_url: str) -> str:
    """The `--mcp-config` payload: the bot's own ask server, at this turn's own path. claude takes
    its MCP config as JSON on the argv — opencode cannot, which is why the shape lives here rather
    than in the frontend that hosts the server (AD-31)."""
    server = {"type": "http", "url": ask_url}
    return json.dumps({"mcpServers": {ASK_SERVER_NAME: server}})


def _output_args(stream: bool) -> list[str]:
    """How the CLI should talk back. Streaming needs all three flags together: `stream-json`
    alone only emits a line per COMPLETED message, so a single-message answer would still show
    nothing until the end — `--include-partial-messages` is what carries the token deltas, and
    `--verbose` is required by the CLI alongside stream-json (measured 2026-07-27)."""
    if stream:
        return ["--output-format", "stream-json", "--verbose", "--include-partial-messages"]
    return ["--output-format", "json"]


class ClaudeBackend(CliBackend):
    name = "claude"

    def build_args(self, prompt: str, session_id: str | None, options: TurnOptions) -> list[str]:
        """Plain --resume, no fork: keeps one lineage (same id, same transcript) per AD-3.
        Fork was only needed in the old bot's --bg era, where a live agent locked the id.
        mode=plan -> --permission-mode plan (agent plans, no edits); build -> bypassPermissions."""
        binary = binaries.resolve("claude")
        perm = "plan" if options.mode == "plan" else "bypassPermissions"
        args = [binary, "-p", "--permission-mode", perm]
        args.extend(_output_args(options.stream))
        add_flag(args, "--model", options.model)
        add_flag(args, "--effort", options.effort)
        if options.ask_url:
            config = _mcp_config(options.ask_url)
            add_flag(args, "--mcp-config", config)
            # Only the bot's own ask server: without this the turn would also load whatever MCP
            # servers Lucas has configured for interactive Claude Code, which is a different
            # tool surface than the one this turn was costed and reasoned about with.
            args.append("--strict-mcp-config")
        if session_id:
            add_flag(args, "--resume", session_id)
        else:
            add_flag(args, "--name", options.title)
        args.append(prompt)
        return args

    def capabilities(self) -> Capabilities:
        """A handful of aliases — small enough that `favourites` IS the whole catalogue and
        the drill-down never opens. The opposite of opencode's 478 (SPECS AD-11)."""
        models = list(_MODELS)
        return Capabilities(modes=list(_MODES), favourites=models, groups={"claude": models})

    def efforts(self, model: str | None = None) -> list[str]:
        """Same ladder whatever the model, so the argument is accepted and ignored."""
        return list(_EFFORTS)

    def last_response(self, session_id: str, cwd: str) -> str:
        """Full text of the session's last answer, read from the transcript — lets /resume
        re-anchor a session by showing where it left off, not just its title."""
        directory = _project_dir(cwd)
        path = directory / f"{session_id}.jsonl"
        text = ""
        if path.is_file():
            lines = transcript.tail_lines(path)
            text = transcript.last_response_text(lines)
        return text

    def occupancy(self, session_id: str, cwd: str) -> int | None:
        """How full the window is after the turn, from the transcript's LAST assistant message.
        One message is one API request, so its `usage` is occupancy; the run summary's
        `modelUsage` is a sum over requests and is spend (b3, see `_context_of`)."""
        directory = _project_dir(cwd)
        path = directory / f"{session_id}.jsonl"
        used = None
        if path.is_file():
            lines = transcript.tail_lines(path)
            used = transcript.last_context_used(lines)
        return used

    def env(self, options: TurnOptions) -> dict | None:
        """The options are accepted and ignored: claude's ask config rides on the argv, so nothing
        here is per-turn (AD-31 — opencode is the provider that needs them).

        AD-8 (revised): Claude Code's native picker hides sessions whose ORIGINATING
        entrypoint is `sdk-cli`, which is what a bare headless `-p` records. The entrypoint
        comes from this env var, not from the flags — setting it makes bot-created sessions
        show up in the VSCode/terminal picker like any other. Verified live 2026-07-23.

        MCP_TOOL_TIMEOUT is the ask_user round trip's ceiling (F4 Stage 4)."""
        return {"CLAUDE_CODE_ENTRYPOINT": _ENTRYPOINT,
                "MCP_TOOL_TIMEOUT": str(_TOOL_TIMEOUT_MS)}

    def supports_ask(self, options: TurnOptions) -> bool:
        """Measured 2026-07-27: in plan mode the CLI answers an MCP tool call with "Cannot call
        mcp__aiwbot__ask_user while in plan mode", and `--allowedTools` does not lift it — plan
        mode blocks the whole MCP surface, not just edits. So the tool is offered in build mode
        only; offering it in plan would spend a turn on a call that cannot land."""
        return options.mode != "plan"

    def stream_parser(self) -> StreamParser:
        return StreamParser()

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)

    def list_sessions(self, cwd: str) -> list[dict]:
        """Read the canonical store (~/.claude/projects/<cwd>/*.jsonl) so the picker shows
        every resumable session for cwd — including ones started in VSCode, not just the bot's."""
        directory = _project_dir(cwd)
        items: list[dict] = []
        if directory.is_dir():
            for path in directory.glob("*.jsonl"):
                item = _session_item(path)
                items.append(item)
        return items
