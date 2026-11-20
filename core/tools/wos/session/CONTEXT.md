# session
> What a session costs and what fills it, read from the local transcripts. No network, no model.

These tools replay local transcripts through [`session_log.py`](session_log.py). Claude logs are the default; `usage` and `context` accept `--provider codex --session <id>` for native logs. Recorded input includes cache; cumulative usage is not current context. Native prices are Standard API-equivalent, not subscription bills.

Quote neither report from memory — re-run the command. The cost work's lesson was four false claims from a stale read.

## Three rules that make the attribution honest

1. **Per-turn context is exact; what *entered* is only known in characters.** The chars-per-token ratio is measured per turn, not assumed as a global `/4`. `context` prints the measured ratio and what it implies: well under ~3.5 means tokens enter that the transcript doesn't log, spread across the reported rows in proportion — read the shares as shares of logged material.
2. **A blocking gate is a failed `tool_result`, not an attachment** — scanning only attachments undercounts by two orders of magnitude. Guarded by `test_a_blocking_gate_is_counted_from_the_failed_tool_result`.
3. **A worker's own transcript marks EVERY record `isSidechain: true`**, so the skip that is right for a parent empties the worker. Both `session_log.walk` and `session_turns.responses` take it as a parameter for that reason; it cost the subagent report its whole population once.

For Claude, `context` separates instruction files measured on disk from the residual. Both readers use `session_turns.events`.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`context`](context) | — | — | what fills the context window: what is already in it at turn 1, what the CONTEXT.md chain costs, what grows it turn over turn, and what a subagent starts with. Reads the local transcripts; no network, no model. |
| [`reads`](reads) | — | — | which files a session reads, how often, and how much each re-read cost. Reads the local transcripts; no network. `--span` reads the matrix instead, which is recorded at the read and therefore answers for every harness and across sessions. |
| [`session_cost.py`](session_cost.py) | [`session_cost.pyi`](session_cost.pyi) | `priced`, `turn_components`, `turn_cost` | session_cost.py — the price of a turn. The one place rates live. |
| [`session_log.py`](session_log.py) | [`session_log.pyi`](session_log.pyi) | `project_name`, `label`, `att_chars`, `blocks`, `output_chars` | session_log.py — replay local transcripts and attribute each turn's context growth. |
| [`session_reads.py`](session_reads.py) | [`session_reads.pyi`](session_reads.pyi) | `kind_of`, `file_reads`, `weights` | session_reads.py — which files a session read, how often, and what each read served. |
| [`session_trace.py`](session_trace.py) | [`session_trace.pyi`](session_trace.pyi) | `spawns`, `clock`, `loudest`, `main_cost` | session_trace.py — what a session DID: who it spawned, where its clock went, what came back loudest. |
| [`session_turns.py`](session_turns.py) | [`session_turns.pyi`](session_turns.pyi) | `trusted_model`, `paths_for`, `events`, `responses`, `turns` | session_turns.py — what counts as ONE assistant turn, and how much of it lands in the thread. |
| [`usage`](usage) | — | — | where session spend goes: by model, by context size, by billed component, and what one more turn costs. Reads the local transcripts; no network, no model. |
<!-- routing:end -->
