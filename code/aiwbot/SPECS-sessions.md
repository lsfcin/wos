# Sessions and lineage
> Where a session lives, who can see it, and how a resume keeps one lineage.
> governs: backend/, frontend/ session listing

### AD-6 — Session listing sources from each backend's own store, not a private registry
The `/resume` picker aggregates `AgentBackend.list_sessions(cwd)` across backends so it sees sessions started anywhere, not just ones the bot created. Stores: **claude** = `~/.claude/projects/<cwd with / → ->/*.jsonl` (one file per session, id = filename stem, timestamp = mtime); **opencode** = `~/.local/share/opencode/opencode.db` sqlite `session` table (top-level rows where `parent_id IS NULL`, `time_updated` is ms). The bot's own `config.json` registry is now only side-state — sticky `mode`, `reply_map`, and an `adopt()` cache (backend+title) written for shown sessions so a later tap resolves the backend for reply-to-continue.

### AD-7 — Claude Code's picker title is the `aiTitle` event (not the opening prompt)
Discovered live (2026-07-22). A session's transcript carries a recurring `"aiTitle":"…"` jsonl event — the AI-generated title Claude Code's own `/resume` shows (e.g. `Resume video tool core M4 implementation`). The **latest** occurrence is the current title. Deriving a title from the opening `last-prompt` instead (as the first cut did) yields ugly labels like `[A06] ## RESUME —`. Prefer `aiTitle` (tail-scan), fall back to `lastPrompt`.

### AD-8 — `--name` does NOT make a headless `-p` session visible in Claude Code's picker
Discovered live (2026-07-22). A bot-created session passed `--name "JUST A TEST"` appeared **only** in the bot's own `/resume` — never in VSCode `/resume` nor terminal `claude --resume`, despite a valid `.jsonl` transcript existing in the project dir. So `-p` sessions are systematically hidden from Claude Code's native picker by a filter internal to the (closed) extension/CLI — the name flag doesn't override it. Making bot sessions natively resumable elsewhere is an open investigation (ROADMAP), not a solved feature; may be impossible from outside the extension.

**SOLVED 2026-07-23 — it was an env var all along.** `CLAUDE_CODE_ENTRYPOINT` decides the recorded entrypoint; the `-p` flag does not. A bare headless run under systemd inherits nothing → `sdk-cli` → hidden. Setting `CLAUDE_CODE_ENTRYPOINT=claude-vscode` on the subprocess makes a bot-created session appear in the native VSCode/terminal picker like any other. Verified live: two headless `-p` sessions created seconds apart, one with the var (`8c5aabce`, origin `claude-vscode`) and one without (`26d440e7`, origin `sdk-cli`) — the first is listed by `claude --resume`, the second is skipped.
`ClaudeBackend.env()` now returns it (the boundary gained `CliBackend.env()` + `run_capture(extra_env=…)`, so this stays provider-specific data, not a global). The value `cli` is **rejected** — it silently falls back to `sdk-cli`; only `claude-vscode` works.

The filter keys on the session's **originating** entrypoint, not later entries: a session created interactively stays listed even after headless `-p` turns append to it, and a session born `sdk-cli` stays hidden even once `claude-vscode` entries are appended. So the var matters at session creation (`/new`, explicit or via the "bot" prefix); already-created bot sessions stay hidden forever.

Superseded reasoning kept below, since the sub-findings still hold:

1. **The filter is real and `--name` does not beat it.** Captured the terminal picker's actual list and diffed it against `~/.claude/projects/-mnt-workspace/*.jsonl` sorted by mtime: every `claude-vscode` /`cli` session appears in exact mtime order, and **every** `sdk-cli` session is skipped — including `5fbc1770`, which *does* carry a `custom-title` record written by `--name`. So `--name` reaches the store but not the picker. The discriminator is `entrypoint` (`sdk-cli` for any `-p`/SDK invocation, stamped by the CLI itself; headless turns also uniquely carry `promptSource:"sdk"` + `permissionMode`).
   The bot has no flag to change it → **cannot be listed** in Claude Code's native picker.
2. **But bot sessions ARE resumable by explicit id.** `claude --resume 5fbc1770-…` from the terminal resumed a bot-created session and answered normally (verified live). They are unlisted, not inaccessible. → Hence the **reattach hint**: the `/resume` anchor message shows a copyable `<code>claude --resume &lt;id&gt;</code>` (`format.reattach_cmd`, provider as data — opencode maps to `opencode -s &lt;id&gt;`). That is the sanctioned escape hatch out of the bot.
3. **Why bot sessions once DID show up in VSCode** (Lucas's recollection, reconciled): the old `--bg` era started each turn as a **background agent**, which registers in the live roster `~/.claude/sessions/<pid>.json` (`kind`, `entrypoint`, `name`, managed by `claude agents`) and thus surfaced in the extension *while running*. That registration is pid-scoped and dies with the process, and it is exactly what forced `--fork-session` (AD-3) → one extra session per message. Visibility and single-lineage were a direct trade-off; Phase B chose lineage.

Native visibility does not require a Claude-Code-native transport — the env-var fix above is the other path. Remote Control / Channels stay rejected for lock-in ([REFS.md](REFS.md)).

### AD-12 — opencode's store answers the picker, but only per message for context %
Picker parity with claude (3-line entry: title / preview / meta) reads opencode's sqlite:

| bit | source |
|-----|--------|
| mode | `session.agent` |
| model | `session.model` JSON → `providerID/id`, the same form `opencode models` and models.json use |
| context window | `models.json` → `limit.context` |
| preview + context used | last `message` with `role=assistant`: its `type=text` parts, and `data.tokens` |

Two traps, both hit live:
1. **`session.tokens_*` are lifetime totals, not occupancy.** A real session summed to 350 927 against a 200 000 window — 175%. Occupancy is per message (`input + cache.read + cache.write`, the same formula AD-9 uses for claude), so it comes off the last assistant message.
2. **`part` rows of `type=text` include the user's message and injected system-reminders.**
   Filtering by the parent message's `role` is what stops the preview quoting Lucas back at himself.

Because those two need a query per session, the boundary gained `session_detail(session_id, cwd)`:
`list_sessions` stays the cheap index, and the picker asks for detail only on the page it renders — 3 sessions, not the 59 that exist.

### AD-15 — systemd's PATH is the login default, so every CLI is resolved explicitly
Found via a wrong error message, 2026-07-23: tapping **model** with harness=opencode answered "esse modelo não expõe controle de esforço". Two faults stacked. The visible one was a single generic message used for any empty value list. The real one: `systemd --user` runs with the login PATH, which does **not** carry the per-tool bin directories a shell rc adds — `opencode` lives in `~/.opencode/bin` and was simply invisible to the service. `opencode models` never ran, the catalogue was empty, and the picker had nothing to show.

The same gap would have failed any opencode **turn** outright, since `build_args` emitted a bare `"opencode"` for `create_subprocess_exec`. Only claude worked, and only because it resolved its binary explicitly already.

`backend/binaries.py` now does that resolution for every backend: PATH first (so a shell override still wins), then the known install locations per tool. `resolve()` raises, `find()` returns None for callers that degrade. Verified inside a real `systemd-run --user` unit: 458 models listed, previously 0. The count differs slightly from a shell's 478 because a couple of providers key off environment the service does not inherit — which is correct behaviour, since the picker should offer only what the process running the turn can actually reach.

### AD-31 — opencode asks through its config, not through a flag (2026-07-29, checked live)

Measured against opencode 1.18.7 before any code was written, the same way AD-27 was measured, and it contradicted three of the audit's guesses. Everything below is from the binary and from three `--format json` turns (~$0.004 on `deepseek-v4-flash`), not from documentation:

- **There is no `--mcp-config` flag.** `opencode run --help` has none, and `opencode mcp` only *manages* servers. So the per-turn config cannot ride on the argv at all — the asymmetry with claude is not "a file instead of a string", it is **env instead of argv**.
- **`OPENCODE_CONFIG_CONTENT` carries the whole config inline**, as JSON, so no temp file and nothing to clean up. Shape: `{"mcp": {"aiwbot": {"type": "remote", "url": …, "timeout": ms}}}`.
- **`opencode mcp add` writes the GLOBAL config and ignores `OPENCODE_CONFIG_DIR`** (verified by running it: it edited `~/.config/opencode/opencode.jsonc`, which had to be restored by hand).
  The bot must never call it — a per-turn server written to the user's own config would outlive the
  turn and point at a dead port from his interactive sessions.
- **The tool reaches the model as `aiwbot_ask_user`**, not claude's `mcp__aiwbot__ask_user`. Nothing in the bot depends on the name, but an error text quoting it will differ per provider.
- **The tool call dies at ~60 s by default** — measured 62 s, announced as `notifications/cancelled` and then reported by the agent as *"a ferramenta retornou timeout"*, which ends the turn on an apology instead of a question. **No env var lifts it** (the binary has no MCP timeout variable;
  `MCP_TOOL_TIMEOUT` is claude's alone). What does is the **per-server `timeout` field** in the
  config — resolution order in the binary is `mcp[name].timeout ?? experimental.mcp_timeout ??
  default`. Verified: with `timeout` set, a 120 s hold survived, the answer was delivered, and the
  turn's final text was the answer Lucas would have tapped.
  So AD-27's invariant — *the wait that ends first is always the bot's* — holds for opencode too,
  but it is bought with config where claude buys it with env.
- **`--agent plan` calls the tool and completes the round trip.** The MCP block that AD-28 was built around is claude's alone.
- `OPENCODE_ENABLE_QUESTION_TOOL` exists (opencode's own native question tool, off by default) and must stay off: its question goes to the TUI, which for a headless bot turn is nowhere.
- **Its streaming is COARSE**, measured on the first live streamed turn: one `text` part per STEP, never per token (arrivals at 11.8 s / 15.5 s / 35.0 s of one turn; a short single-step answer is exactly one event at the end). So a streamed opencode turn grows bubble-per-step where a claude turn grows continuously. Nothing to fix — throttle, sealing and pacing all treat whole segments correctly (`partial=False`) — but do not promise the two providers feel the same.

Two boundary consequences, both of which are why this is a decision and not a patch. `CliBackend.env()` takes no options, so a **per-turn** env value has nowhere to come from — it becomes `env(options)`, because stashing the turn on the backend breaks as soon as two turns overlap, and they do.
And `TurnOptions.mcp_config` is claude's JSON under a provider-agnostic name; the honest field is the **URL** (`ask_url`), with each backend wrapping it in its own config shape.
