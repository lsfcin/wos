# Hooks — Specs
> What each gate blocks, what the hooks write, and the contract a new agent's shim must satisfy.

## The law lives in file_law.py / schema_law.py / limits.env, never in a checker

A checker that restates any of these is the drift the checkers exist to catch, and it has bitten
three times. **The dangerous shape never looks like drift: a tool that knows it is overriding the
law has found a gap in the law, not a special case of its own.** The tell is a checker whose
docstring explains why it disagrees with what it just asked. A module here reaches that law with
`sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`; the suite gets it once, from
`core/tools/test/conftest.py`.

## Git pre-commit (`pre-commit`)

Applied globally via `core.hooksPath`, so it fires on every `git commit` in **every** repo under this
workspace. Stage order and the one place a commit is refused: [`commit/CONTEXT.md`](commit/CONTEXT.md).

- Warns and then blocks on the length of any authored file, code and writing alike, via
  `checks/line_counts.py` over staged files — the same module that runs standalone. Both thresholds
  are [`limits.env`](limits.env)'s answer and which files are authored is
  [`file_law.py`](file_law.py)'s, never a checker's: the copy that stood here named the old pair for
  five days after the law moved. A file waives the **warn** — never the block — with a
  `warn-exempt: <reason>` line of its own.
- Hard-blocks cross-module imports that bypass the facade, via `facade/check-facade-imports.py`.
- Auto-syncs each staged directory's `CONTEXT.md` routing block, and generates `.pyi`, `.d.ts` and
  `.dart.api` — all staged with the commit.
- `verify:fast` contract: a project declaring that script must be green, or the commit is blocked.
- `checks/check-duplication.py`: jscpd over the repo, blocking clones that involve a staged file.
- Spec-driven module gate: a new `CONTEXT.md` under `code/` must declare `> spec: <file>` or
  `> spec: none`. Ratchet — existing modules are grandfathered.
- `checks/type-gate.py`: a staged `.md` must be a known type or a well-shaped instance, sitting where
  its type is allowed. Ratchet — only what a commit **adds**. Law parsed from
  [`../SCHEMA.md`](../SCHEMA.md), never restated.
- `checks/citation-gate.py`: a roadmap item number may not appear outside `ROADMAP*.md`. **Not a
  ratchet** — swept to zero 2026-08-16. Completion is deletion here, so a cited number points at
  nothing the day the item lands; cite the section instead, by its *shape* and never the bare word.
- `git/gitignore-self-heal.sh`: a new domain subdirectory carrying a `CONTEXT.md` gets its
  `!<domain>/<dir>/` allow line written, and **then stops the commit** if that directory holds files
  git could not see. Ruled 2026-08-19 (Lucas): **a commit hook that stages what the caller did not
  is worse than the bug it fixes.**

### Branch drift

**HEAD is shared mutable state between parallel sessions.** A parallel session switches the shared
checkout mid-flight and your commit lands on *their* branch, auto-pushed there. **The branch reads
correct at session start**, which is why no start-of-session check can catch it.
[`git/branch_marker.py`](git/branch_marker.py) records the branch at `SessionStart`; the pre-commit
path warns when HEAD no longer matches. Three properties carry it: **warn, never block**, because a
deliberate switch is legitimate; **once per divergence**, since a repeated warning is one people
learn to skip; and **one marker per repo, not per session**, because `check` runs inside a git hook
with no session id to pair with. The warning prints its own non-destructive recovery. Never reset or
force-push theirs, and never `git checkout` your branch back — that yanks HEAD out from under them,
the same defect pointed the other way.

**No exemptions for vendored third-party code.** A `.vendor` marker switching the gates off was
rejected (2026-07-23, Lucas: *"even thirdparty solutions, once brought to our w-os should comply with
our rules. opening exceptions is quite dangerous"*). Vendoring means adopting and adapting: split
what is too big, and record the deviations a future re-sync merges against.

## A marker is asked about, never string-matched across the shell/Python boundary

**Whichever side WRITES a session marker answers questions about it.** `Path.resolve()`, a hook
payload and `readlink -f` produce three spellings of one Windows path, matched by nothing, so a gate
blocked every read while its message promised that reading the interface would unlock it. **A gate
that can only block is the mirror of one that can only pass**, and both read as working. So: **the
module owning the marker owns the comparison**, and every reader asks `hook_input`.

## Agent lifecycle gates

Bound from `.claude/settings.json`, and by the equivalent registration in each other provider's
shim. Every one spawns through [`../run`](../run), which is the shim contract in one line —
`sh ${CLAUDE_PROJECT_DIR}/core/run <path-relative-to-core/> [args]`.

**A shim carries no machine-specific string, and that is the whole reason `run` exists** — it picks
this clone's venv layout, exports `PYTHONIOENCODING=utf-8`, and answers `--python` for a caller that
must spawn Python inline. Why the bare word `python3` is banned is in [`../run`](../run)'s own head;
`test_no_shell_hook_spawns_the_bare_word_python3` holds it at zero.

### One dispatcher, and the table it reads

Every `PreToolUse` gate is registered once, as [`dispatch.py`](dispatch.py): it reads stdin once,
asks [`hook_input.capability`](hook_input.py) once, and runs in-process the gates that capability
selects from [`gates.txt`](gates.txt) — which also tells
[`trigger/trigger_law.py`](trigger/trigger_law.py) when each fires. Separate `command` entries cost
roughly eight times the dispatcher's per-call latency (b20260905); why they were also five
hand-copies of one table is in [`gates.txt`](gates.txt)'s own head.

Four rules survive the collapse, and `test_b20260905_*` holds each. **A blocking gate exits 2 having
written its own reason to stderr**, passed through untouched — the dispatcher never composes,
summarises or prefixes a rejection, and stops the chain there. **A gate that dies takes only
itself**: traceback to stderr, the chain continues, exit 1 and never 2, because a broken gate may not
block a call it was only observing. **A gate the table calls `informs` may not block**, and is
refused loudly if it tries. **Informing gates merge into ONE `hookSpecificOutput`**, because a hook's
stdout is parsed as a single document and a second would be heard by nobody.

| Script | Selected by | Behaviour |
|--------|-------------|-----------|
| `read/context-gate.py` | read, write | **Blocks** until the target folder's `CONTEXT.md` chain was Read this session; on a read it also names the current stub, so one batch clears both read gates. Session-deduped; `CONTEXT.md`/`AGENTS.md` exempt |
| `read/pre-read.py` | read | **Blocks** reading a source file while its interface is current, naming the unread chain alongside it — both read gates exit 2 on one read and the harness reports only the first, so each names the whole set. Warns when the interface is stale; reading it unlocks the source |
| `checks/first-line-gate.py` | write | **Blocks** a new file whose first line does not say what it is, and a new `CONTEXT.md` with no `>` description on line 2 |
| `checks/size-gate.py` | write | **Blocks** an edit pushing an authored code file past either block cap, lines or characters |
| `facade/facade-scan.py` | write | **Informs** — the exports the target module's facade already declares; warns if that list is empty |
| `facade/facade-gate.py` | write | **Blocks** edits to a `code/` module file until the nearest facade was Read this session |
| `checks/issues-gate.py` | write | **Blocks** flipping a bug to FIXED, or deleting its section, without a matching `test/**/b<N>-*` regression spec |
| `read/spec-read-gate.py` | write | **Blocks** editing a spec-locked module (`CONTEXT.md` `> spec:` + `SPECS.md` `status: locked`) until its `SPECS.md` was Read this session; nudges on new files in spec-less `code/` modules |
| `read/bash-context-gate.py` | shell | **Blocks** commands naming workspace files in folders whose chain is unread — this closes the `cat`/`grep` bypass |
| `checks/heredoc-gate.py` | shell | **Warns, never blocks** — a heredoc writing a workspace file meets none of the write gates. Silent for stdin-to-an-interpreter, which writes nothing |

Registered on their own moments, outside the table: `read/agent-context.py` (PreToolUse `Agent`,
SubagentStart) **induces, never blocks**, handing a worker the `>` line of each folder its prompt
names — its exemption from the chain gate is [`../SPECS.md`](../SPECS.md) § AD-13;
`facade/facade-tracker.py` and `read/context-tracker.py` (PostToolUse) record the reads the gates
above consume; `post-edit.sh` (PostToolUse) regenerates interfaces, scaffolds `jsconfig.json` /
`tsconfig.json` and runs the routing sync; `session/precompact-wipe.py` (PreCompact) wipes the
seen-markers; `session/session-prune.py` (SessionStart) drops stale markers, and
`session/mirror-heal.py` regenerates skill mirrors there while **warning without writing** when a
harness permission config no longer matches `core/profile.txt`. `compact/bash-compact-rewrite.py`,
registered once at user scope, **rewrites, never blocks**.

**Why one of them only warns.** A `PreToolUse` hook fires *after* the model emitted the tool call, so
by the time `heredoc-gate.py` sees a long `cat >` payload those tokens are already billed; blocking
makes the turn emit them again as a `Write`, and the gate exists to change turn N+1. **Any gate whose
subject is what was already sent has this shape; one whose subject is what is about to happen on disk
should still block.** It warns through `hookSpecificOutput.additionalContext`, delivered **to the
model** on exit 0 with the tool still running — the only non-blocking channel that reaches it, since
exit-0 stdout is transcript-only and `systemMessage` addresses Lucas rather than the agent. **Every
"Informs" hook uses it**, asserted by
`test_an_informing_hook_speaks_on_the_channel_that_reaches_the_model`. And **a
`.claude/settings.json` hook edit is live in the session that made it**. Both verified by running
them, neither documented.

## Generated artifacts

What each generator writes is specified beside it: [`stubgen/SPECS.md`](stubgen/SPECS.md) for
interfaces and the size-cap bypass, [`routing/SPECS.md`](routing/SPECS.md) for the routing block and
first-line descriptions. Three rules stay here, because the root's law owns them.

**A file a tool writes is not a file anyone authored.** A file is **authored** — every size, shape
and first-line rule applies — or **vendored** and exempt because upstream chose its layout, or
**generated**, which is neither. [`generated.txt`](generated.txt) declares what our tools write, a
**named, reviewed glob list, never a heuristic**, each entry naming its generator. **Why the
exemption is safe here and not in general:** the artifact has a test that its generator reproduces
it byte for byte (`--check`). An entry without that is a hand-edited file in a costume.

**A generated BLOCK inside an authored file is exempt the same way, and only inside its markers.**
`generated.txt` answers for whole files; `file_law.generated_spans()` answers for the `:start`/`:end`
span, and every reader asks it rather than spelling the markers. A finding there has no legal fix —
hand-editing one is forbidden outright — so reporting it is reporting what nobody can act on. Five
checks learned that separately on 2026-09-11, all on `ISSUES.md`'s quoted red-suite log.

**Finished-work writing is blocked on what a commit adds.** `entropy/entropy_list.py` carries the
detector and `checks/type-gate.py` calls it on `staged_added_files()`, so a file **arriving** with a
dead item is rejected while the inherited queue stays the dashboard's, under
`test_corpus_ratchet.py`'s ceiling. That split is the rule for every Level 0 check here: **a gate that
fails on the day it lands trains its reader to ignore it.** [`core/SPECS.md`](../SPECS.md) § AD-15
makes blocking — not the mere existence of a detector — what licenses deleting the writing.

## Canonical behaviour, and the contract a new agent's shim must satisfy

Canonical behaviour lives in neutral files under `core/hooks/` and [`AGENTS.md`](../../AGENTS.md). A
provider-specific file is a shim, a discovery point or startup wiring — **never a second copy of a
rule** — and is either **ENFORCED**, able to block a read, an edit or a commit, or **INDUCED**, guidance
the agent may ignore. ENFORCED, one registration each:
`.github/hooks/workspace-policy.json` (Copilot lifecycle), `.opencode/plugins/workspace-policy.js`
(translates `tool.execute.*` and `experimental.session.compacting` onto the dispatcher),
`.zcode/config.json` (direct spawns, no adapter), `.agents/hooks.json` (delegates to
`antigravity_policy.py`). INDUCED: `AGENTS.md` and the one-line shims pointing at it
(`.github/copilot-instructions.md`, `GEMINI.md`), `opencode.json` and `.vscode/settings.json`
(discovery anchors), and each harness's `skills/` mirror, generated by `sync-skills`.

Three hook points cover the whole surface: **PreTool (any tool)** → `sh core/run hooks/dispatch.py`;
**PostTool (Edit)** → `bash core/hooks/post-edit.sh`; **PostTool (Read)** →
`sh core/run hooks/facade/facade-tracker.py` and `sh core/run hooks/read/context-tracker.py`. The
payload is JSON on **stdin** for pre-hooks and in **`CLAUDE_TOOL_INPUT`** for post-hooks, `file_path`
absolute, and exit code **2** is a hard block with **stderr** as the message shown to the agent.

**Register on every tool, and let the payload decide.** A shim that filters by tool name is a
whitelist that goes stale the moment its harness adds a tool — silently, in the direction where
nothing reports it. That is b20260901: a PowerShell tool beside Bash met no read gate, so the layer
was weaker on one operating system with nothing saying so. The matchers are `.*` and the dispatcher
asks
[`hook_input.capability`](hook_input.py) what the call DOES: a command line runs one, a path plus new
content writes it, a path alone reads it. **An empty field is omitted, never sent empty** —
capability asks whether a content key is *present*, so `content: ""` on a read runs the write gates.

**A shim must pass a session-stable id** or the markers never dedupe and every gate fires on every
call. Worked examples, each translating its harness's argument names into a canonical payload and
stopping there: `copilot/copilot-pre-tool.py`, `antigravity/antigravity_policy.py`,
`.opencode/plugins/workspace-policy.js`.

**Every gate in `gates.txt` reaches every harness by construction** — one registration, one table,
and `test_every_shim_reaches_the_dispatcher` fails any shim that stops naming it — as do the
trackers and `post-edit.sh`. What still differs never went through the dispatcher: the git-only
stages above reach the other harnesses only because git does, and **lint is the live gap**. Event
remaps: no `SubagentStart` in zcode, so `agent-context.py` rides PreToolUse `Agent|Task`; no
`PreCompact`, so `precompact-wipe.py` rides SessionStart `^compact$`.

**A claim about coverage is checked by `test_shim_paths.py`**, which proves a path **resolves** and
never that a gate **fires**. A new runtime's shim owes the contract above and an entry in that file's
`SHIMS`. A shim with no entry is unchecked, the state opencode and Copilot were both in.
