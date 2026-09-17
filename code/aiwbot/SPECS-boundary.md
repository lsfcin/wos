# The backend boundary
> The one interface every coding-agent CLI becomes, and what it must pin.
> governs: backend/

### AD-1 — The boundary is `AgentBackend.send() -> AsyncIterator[AgentEvent]`
Every backend is a CLI subprocess emitting JSON we normalize into `AgentEvent(kind, text, tool,
session_id, cost_usd)`. `kind ∈ {text, thinking, tool, result, error}`. Minimum contract
(`check_contract`): ≥1 `text` event AND a terminal `result` carrying `session_id`. This is the ONLY
thing the frontend depends on — providers are interchangeable data behind it.

### AD-2 — `CliBackend` holds `send()` once; subclasses supply `build_args` + `parse`
Avoids per-backend duplication of the subprocess loop and run-result handling (`proc.events_from_run`).
`parse_events` stays a module-level pure function per backend → free to unit-test with fixtures.

### AD-3 — Both backends keep one lineage; the frontend still chases `result.session_id`
**Revised 2026-07-21** (Phase B). Both backends now resume into a SINGLE lineage — one session id,
one transcript, one VSCode entry that grows in place: **claude** via plain `--resume <id>` (same id
back), **opencode** via `-s <id>` (same id). Earlier this doc claimed `--fork-session` was mandatory
for claude — that was true only in the old bot's `--bg` era, where a live/registered background agent
locked the session id and refused a plain `--resume`. Phase B dropped `--bg`: `send()` is a one-shot
`-p` subprocess that exits after each turn, so the session is never locked between turns and plain
`--resume` succeeds (verified live). Forking was producing cumulative VSCode sessions (N forks = N
entries) for no benefit, so it's gone — this also matches linuz90's SDK design (plain resume, capture
id once; see [[reference_linuz90_bot]]). The frontend still stores the latest `result.session_id` each
turn and the boundary surfaces it uniformly — that contract is unchanged and cheap insurance even though
both ids now happen to be stable. **Edge case**: plain `--resume` IS refused if that exact session is
concurrently open live elsewhere (interactive VSCode / a still-running agent) — the frontend detects
the busy/not-found error and shows a "close it there first" message rather than a raw error.

### AD-4 — cwd must be pinned on dispatch — and `PWD` with it
Subprocesses run with explicit `cwd` (not the daemon's inherited $HOME) or the session registers under
the wrong directory and becomes invisible to later lookups. Carried from the workspace-bot cwd bug.

**Necessary but not sufficient — corrected 2026-07-29 by b4.** `cwd=` on the subprocess sets the
real working directory, and opencode reads **`$PWD`** in preference to it. Under systemd, `PWD` is
whatever the daemon inherited (`/home/lucas`), so every Telegram opencode turn ran its file and shell
tools there AND filed its session there, while `/resume` listed the workspace root — for weeks, silently,
with Lucas's own prompts landing in his home directory. `proc.child_env` now forces `PWD` to the
turn's cwd for every child, applied AFTER each backend's own knobs so no provider can override it.
The general rule: a child inherits two answers to "where am I" and they must not be allowed to
disagree.

### AD-33 — A provider that never names its model is asked for it afterwards (2026-07-29)

An opencode answer's footer named no model. Not a parsing miss: **no line of
`opencode run --format json` names a model anywhere** — not the text parts, not `step_finish`,
which carries cost and tokens but nothing about who produced them. The store does, on the
assistant message (`providerID` + `modelID`).

So the model joins occupancy as a fact read from the provider's own store after the turn, in the
same place and under the same rule (`_attach_measured`, renamed from `_attach_occupancy` now that
it attaches two things): **the store is a fallback, never an override.** claude names its model in
the stream and keeps it. A backend that cannot say leaves the footer to print nothing rather than
invent a name. The pattern generalizes — a third provider that omits a field the footer wants adds
one hook here, not a special case in the frontend.
