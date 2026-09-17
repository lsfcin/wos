# cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse.
from __future__ import annotations
from typing import AsyncIterator
from .base import AgentEvent, LineParser, TurnOptions
from .caps import Capabilities
from .proc import run_capture, events_from_run, silent_run, stream_lines


class CliBackend:
    name: str = "cli"

    def build_args(self, prompt: str, session_id: str | None, options: TurnOptions) -> list[str]:
        raise NotImplementedError

    def parse(self, stdout: str) -> list[AgentEvent]:
        raise NotImplementedError

    def list_sessions(self, cwd: str) -> list[dict]:
        """Default: provider exposes no session store. Backends with one override this."""
        return []

    def last_response(self, session_id: str, cwd: str) -> str:
        """Default: provider exposes no transcript. Backends with one override this."""
        return ""

    def session_detail(self, session_id: str, cwd: str) -> dict:
        """Default: the list already carried everything. Backends whose store needs a
        per-session query put the expensive fields here instead, so the picker pays for
        the page it renders rather than for every session it lists."""
        return {}

    def stream_parser(self) -> LineParser | None:
        """A parser that consumes the CLI's output line by line. Default: none, so a backend
        that has not opted in simply never streams and keeps the batch path verbatim."""
        return None

    def occupancy(self, session_id: str, cwd: str) -> int | None:
        """Context-window occupancy after the turn, read from the provider's own store.
        Default: unknown. Backends that record per-message token usage override this."""
        return None

    def model_used(self, session_id: str, cwd: str) -> str | None:
        """Which model actually ran, for providers whose output never says. Default: unknown, so
        the footer prints whatever the stream reported and invents nothing."""
        return None

    def env(self, options: TurnOptions) -> dict | None:
        """Extra environment for the subprocess. Default: none — backends override.

        Takes the turn's options because for some providers the per-turn config has no flag to ride
        on and must arrive as environment (AD-31). Stashing the options on the backend instead would
        break the moment two turns overlap, and they do — every turn is its own PTB task."""
        return None

    def supports_ask(self, options: TurnOptions) -> bool:
        """Default: no. Asking the user mid-turn needs the CLI to host an MCP server pointed at
        the daemon, so it is opt-in per provider and never assumed from the presence of a flag."""
        return False

    def capabilities(self) -> Capabilities:
        """Default: nothing selectable, so the panel simply shows no rows for this backend."""
        return Capabilities()

    def efforts(self, model: str | None = None) -> list[str]:
        """Default: no effort knob. Backends whose CLI has one override this."""
        return []

    async def send(self, prompt: str, *, session_id: str | None, cwd: str,
                   options: TurnOptions = TurnOptions()) -> AsyncIterator[AgentEvent]:
        args = self.build_args(prompt, session_id, options)
        extra_env = self.env(options)
        parser = self.stream_parser() if options.stream else None
        if parser is None:
            out, err, code = await run_capture(args, cwd, extra_env)
            events = events_from_run(out, err, code, self.parse)
            self._attach_measured(events, cwd)
            for event in events:
                yield event
            return
        async for event in self._stream(args, cwd, extra_env, parser):
            yield event

    async def _stream(self, args: list[str], cwd: str, extra_env: dict | None,
                      parser: LineParser) -> AsyncIterator[AgentEvent]:
        """Yield events as their lines arrive, then the terminal ones.

        Order is load-bearing: `stream_lines` only emits its ("end", …) tuple after the process
        has EXITED, and the terminal events are held until then, because occupancy is read from
        the provider's store and the store is written on exit. Emitting the result event any
        earlier reintroduces b3 (AD-24) as a silent wrong percentage."""
        seen = 0
        err, code = "", 0
        async for kind, payload, status in stream_lines(args, cwd, extra_env):
            if kind == "line":
                for event in parser.feed(payload):
                    seen += 1
                    yield event
                continue
            err, code = payload, status
        events = list(parser.finish())
        if not events and not seen:
            events = [AgentEvent(kind="error", text=silent_run(err, code))]
        self._attach_measured(events, cwd)
        for event in events:
            yield event

    def _attach_measured(self, events: list[AgentEvent], cwd: str) -> None:
        """Facts the stream did not carry, read from the provider's own store once the turn ended.

        Occupancy is a property of the turn's LAST request, never of its total spend — a turn that
        used tools made several requests and each re-read the whole context, so any sum over them
        measures money, not how full the window is (b3). The MODEL is the same shape of gap for
        opencode, whose JSONL names one nowhere, which is why its answers arrived with a nameless
        footer (Lucas, live 2026-07-29). Both are read here rather than guessed, and neither
        overwrites something the stream did report."""
        for event in events:
            if event.kind == "result" and event.session_id:
                measured = self.occupancy(event.session_id, cwd)
                if measured is not None:
                    event.context_used = measured
                if not event.model:
                    event.model = self.model_used(event.session_id, cwd)
