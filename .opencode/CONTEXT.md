# opencode
> opencode configuration, plugins, and skills for this workspace.

This file documents the plugin internals. What it must satisfy — the canonical
gates, the shim contract, the coverage table — is
[`core/hooks/SPECS.md`](../core/hooks/SPECS.md); the install check is
[`SETUP.md`](../SETUP.md) § Already wired.

## Workspace policy plugin

`.opencode/plugins/workspace-policy.js` mirrors the workspace behavioral hooks
defined in `.claude/settings.json` so opencode enforces the SAME policies as
Claude Code: first-line comment, line-count limits, CONTEXT.md line-2
description, facade-first reads, interface-first source reads, and interface
regeneration after edits.

The existing `core/hooks/*` scripts remain the single source of truth for policy
logic. The plugin only TRANSLATES opencode's `tool.execute.before`/`after`
events into the stdin-JSON + `CLAUDE_TOOL_NAME`/`CLAUDE_TOOL_INPUT` env schema
the scripts already expect, and maps Claude's exit-2 block convention to
opencode's `throw` from `tool.execute.before`. Every payload carries a
session-stable id — `opencode${process.pid}`, the Copilot `copilot<host-pid>`
pattern — so the seen-markers dedupe per session; `hook_input.py`'s ppid
fallback lands on the terminal, which leaks "already seen" across every session
that terminal ever ran. Every spawn asks `core/run --python` for the
interpreter (the platform boundary): the bare word `python3` is the spelling that
silently switched the whole plugin off on a Windows clone — the Store alias
prints an advert, exits 9009, and the feature check read as "feature off".

Design lifted from the parallel `core/hooks/copilot/copilot-pre-tool.py` and
`core/hooks/copilot/copilot-post-tool.py`, which already solve the same translation
problem for a non-Claude agent. Field-name lists (`PATH_KEYS`,
`CONTENT_KEYS`, `OLD_KEYS`, `NEW_KEYS`) are reused verbatim.

### Event → script mapping

| opencode event | Script | Block via |
|---|---|---|
| `tool.execute.before`, any mapped tool | `core/hooks/dispatch.py` | exit 2 → throw |
| `tool.execute.after`, `read` | `facade/facade-tracker.py`, `read/context-tracker.py` | n/a (no block) |
| `tool.execute.after`, `edit`/`write`/`apply_patch` | `core/hooks/post-edit.sh` | n/a (no block) |
| `experimental.session.compacting` | `core/hooks/session/precompact-wipe.py` | n/a (no block) |

**Which gates run is not decided here.** `dispatch.py` reads the capability off
the payload and selects from `core/hooks/gates.txt`; this plugin only builds the
payload. The `before` handler carried eleven script rows until 2026-09-05, keyed
on opencode's tool names — a hand-copy of that table, in the tool-name shape
`b20260901` retired.

`bash` and `grep` still get their own branch, because their target is a
`command` and a `path` rather than a `file_path` — a translation, not a policy.
No post-hook for `bash` (same as Copilot — nothing to track after a terminal
command). The compaction hook wipes this session's seen-markers so the
CONTEXT.md chain is re-read after compaction — the PreCompact equivalent.

**An empty field is omitted, never sent empty.** `hook_input.capability()` asks
whether a content key is PRESENT, so a read payload carrying `content: ""` would
read as a write and run the write gates. `buildPayloads` drops empty fields;
`apply_patch` keeps an empty `old_string`/`new_string` pair on purpose, because
it IS a write whose body no gate here can measure.

### Tool-name mapping (opencode → Claude canonical env value)

| opencode tool | `CLAUDE_TOOL_NAME` | matcher group |
|---|---|---|
| `read` | `Read` | read |
| `edit` | `Edit` | edit |
| `write` | `Write` | edit |
| `apply_patch` | `Edit` | edit (paths parsed from `patchText` `*** ... File:` markers) |
| `grep` | `Grep` | gate-only (context-gate; payload carries `path`, not `file_path`) |
| `bash` | `Bash` | gate-only (bash-context-gate + heredoc-gate; payload carries `command`) |

Other opencode tools (`glob`, `webfetch`, `skill`, `todowrite`, …) are not
mapped and pass through untouched. `glob` is ungated on Claude too — parity, not
an omission. opencode exposes no spawn event for `agent-context.py` (Claude
gates it on `Agent`/`SubagentStart`), so a spawned worker is not handed its
folder briefings here.

### stdin vs env-var schema (per script, verified by reading each)

- `pre-edit.py`, `facade-scan.py`, `facade-gate.py`, `pre-read.py` → read JSON
  from **stdin**. Plugin spawns with `spawnSync({input: json})`.
- `post-edit.sh`, `facade-tracker.py` → read JSON from the **`CLAUDE_TOOL_INPUT`
  env var** (not stdin). Plugin sets `env.CLAUDE_TOOL_INPUT = json`.
- `precompact-wipe.py` → reads `session_id` from **stdin** (no tool payload —
  the compaction hook sends `{session_id}` and nothing else).
- All scripts also read `CLAUDE_TOOL_NAME` (values `Read`/`Edit`/`Write`/
  `Grep`/`Bash`); the plugin sets it on every spawn.

### Warning surfacing (known limitation)

opencode has no inline-tool-warning API on `tool.execute.before`. Blocking
messages reach the LLM via `throw` (the only inline channel). Non-blocking
warnings (e.g. `⚠️ INTERFACE STALE` from `pre-read.py`, `💬 FIRST-LINE MISSING`
from `post-edit.sh`) use two channels:

- `client.app.log({ body: { level: "warn", message } })` — server log entry.
- `client.tui.showToast({ body: { variant: "warning", message } })` — TUI toast.

**`warn` unwraps `hookSpecificOutput.additionalContext` first**, because both
channels are read by a person and a gate speaks in that envelope. Found
2026-09-05 by driving the plugin with a synthetic client: every toast was a JSON
document rather than a sentence.

The LLM does NOT see pre-hook warnings; only the user does. Post-hook messages
(`✓ .pyi regenerated`, etc.) are appended to `output.output` on
`tool.execute.after` so the LLM sees them in the tool result (the only inline
channel for after-hooks).

### Load order

Project-level plugin (`.opencode/plugins/`), loaded after global config and
global plugins. Symmetric with `.claude/settings.json` (project-level Claude
Code hooks). No changes to global `~/.config/opencode/` are made.

### Verifying the plugin

Syntax + export check:
`node --input-type=module -e "import('./.opencode/plugins/workspace-policy.js').then(m=>console.log(typeof m.WorkspacePolicy))"` (from the workspace root)

End-to-end smoke test (synthetic client, no opencode process needed): see the
test harness in the session that created this file — it covers seven original
scenarios: read-block-with-pyi, read-allow-no-pyi, write-block-no-comment,
write-block-oversized, write-allow-small, edit-allow-then-post-regenerates-pyi,
read-facade-allow-then-tracker-silent. G6 (context-gate/bash-context-gate/
context-tracker/issues-gate) added three more, verified the same way:
read/bash blocked on an unread CONTEXT.md chain then allowed after the chain
is marked seen via the after-hook, and an edit flipping a ISSUES.md entry
to FIXED without a matching `test/**/b<N>-*` spec blocked once the chain is
seen (context-gate has to pass first to reach issues-gate, same ordering
as `copilot-pre-tool.py`'s `gate()` chain).

To validate inside a real opencode session, start opencode at the workspace root
and run the test plan from the resume prompt: try to read a `.py` with a current
`.pyi` (expect block), write a new `.py` without a first-line comment (expect
block), edit a `.py` past `BLOCK_LINES` (expect block), grep a workspace folder
before reading its `CONTEXT.md` chain (expect block — target is the `path` arg),
edit a `.py` (expect `.pyi` timestamp updates), edit a `CONTEXT.md`-adjacent dir
(expect `context_synchronizer` runs), and after `/compact` the chain gate asks
again (expect `precompact-wipe.py` removed `claude_ctx_seen_opencode<pid>`).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`skills/`](skills/CONTEXT.md) | OpenCode's discovery point for the skill library: generated copies of core/skills, not tracked. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`index.js`](index.js) | [`index.d.ts`](index.d.ts) | — | **facade** — opencode config facade — public surface consumed by plugins/workspace-policy.js. |
| [`agents/craft-high.md`](agents/craft-high.md) | — | — | Craft-flow executor, high level — planning, plan review, architecture, escalated coding. Spawned by the craft flow with a single loop file as input. |
| [`agents/craft-low.md`](agents/craft-low.md) | — | — | Craft-flow executor, low level — mechanical steps (grounding, branch, ship). Spawned by the craft flow with a single loop file as input. |
| [`agents/craft-medium.md`](agents/craft-medium.md) | — | — | Craft-flow executor, medium level — tests-first, code-until-green, user test. Spawned by the craft flow with a single loop file as input. |
| [`jsconfig.json`](jsconfig.json) | — | — | ← add first-line comment |
| [`plugins/jsconfig.json`](plugins/jsconfig.json) | — | — | ← add first-line comment |
| [`plugins/workspace-policy.js`](plugins/workspace-policy.js) | [`plugins/workspace-policy.d.ts`](plugins/workspace-policy.d.ts) | `WorkspacePolicy`, `blockMsg` | Workspace policy plugin for opencode. |
| [`wp-helpers.js`](wp-helpers.js) | [`wp-helpers.d.ts`](wp-helpers.d.ts) | `python`, `buildPayloads`, `buildGrepPayload`, `run`, `warn` | Helpers for the workspace-policy opencode plugin. |
<!-- routing:end -->
