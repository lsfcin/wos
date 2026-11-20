# Capability and model choice
> What a backend declares it can do, and how mode, model and effort are offered.
> governs: backend/ capability declaration, frontend/ pickers

### AD-9 — Context % is free: it already rides in the result object
`claude -p --output-format json` returns `modelUsage[model]` carrying **both** the token breakdown (`inputTokens` + `cacheReadInputTokens` + `cacheCreationInputTokens` = occupancy) **and**
`contextWindow`. We already parse that object every turn, so reporting `X%` costs zero extra tokens —
no `/context` call, no estimation. Plumbed as `AgentEvent.context_used`/`context_window` → `TurnResult` → footer.

Transcripts (`.jsonl`) carry the same usage numbers in snake_case on each assistant message but **not**
the window. So for the `/resume` list the frontend pairs transcript usage with a window *learned* from live turns (`sessions.remember_context_window`, keyed by model) instead of hardcoding per-model constants. Unknown model → the `%` bit is simply omitted, never guessed.

### AD-10 — Both CLIs expose mode, model AND effort; the boundary can carry all three
Verified live 2026-07-23 (`claude --help`, `opencode run --help`, `opencode agent list`, `opencode models`), settling the "unverified" note that was blocking the backend/model/effort design.

| knob | claude | opencode |
|------|--------|----------|
| mode | `--permission-mode plan\|bypassPermissions\|acceptEdits\|auto\|manual` | `--agent <name>`; `build` and `plan` are both **primary** agents (also `compaction`, `summary`, `title`; `explore`/`general` are subagents) |
| model | `--model` — alias (`opus`, `sonnet`, `fable`) or full id | `-m provider/model`; `opencode models` lists **478** across providers (`anthropic/*`, `google/*`, `alibaba-coding-plan/*`, free `opencode/*` levels…) |
| effort | `--effort low\|medium\|high\|xhigh\|max` | `--variant` — "provider-specific reasoning effort, e.g. high, max, minimal" |
| title | `--name` | `--title` |
| fork | (dropped, AD-3) | `--fork` |

Consequences for the design:
1. **The earlier claim that opencode has no plan/build equivalent is false** — it was asserted in `opencode.build_args`'s docstring and repeated in the roadmap. `--agent plan` is a one-flag map.
2. **Capability declaration is still the right shape**, but as a per-backend mapping table, not an open question. What genuinely differs is *cardinality*, not existence: claude's model set is a handful of aliases, opencode's is 478 — so the model picker cannot be one flat keyboard. Provider→model drill-down, or a curated favourites list plus a typed escape hatch.
3. **Effort values do not share a vocabulary** (`low..max` vs `minimal|high|max`), which is exactly why it belongs behind the boundary as provider data — the frontend offers whatever the backend declares.

### AD-11 — Capability declaration: the frontend offers only what a backend declares
Shipped with P2 (plan + measurements: [ROADMAP-p2.md](ROADMAP-p2.md)). AD-10 established that both CLIs expose mode, model and effort; AD-11 is how that reaches a keyboard without the frontend learning any provider's vocabulary.

**The boundary gained two declarations and two knobs.** `TurnOptions` carries `model` + `effort` (opaque strings), and `AgentBackend` answers `capabilities() -> Capabilities(modes, favourites, groups)` plus `efforts(model) -> list[str]`. The frontend renders exactly what comes back and invents nothing, so a value the CLI would reject can't be tapped.

**Effort is asked per model, not per backend, because that is how it varies.** `models.json` declares `reasoning_options` per model in four shapes — `effort` with values (1578 models), `toggle` (939), `budget_tokens` (502), absent (3311) — and the `effort` value sets themselves differ (`low,medium,high` · `high,max` · `minimal,low,medium,high` · `low..max`). claude is the easy case: one `--effort low|medium|high|xhigh|max` ladder for everything. The non-effort shapes declare `[]`, and the panel says so out loud instead of drawing a row of values `--variant` would refuse.

**Cardinality, not existence, is what differs** (AD-10's phrasing) — so the model picker is `favourites` + a `groups` drill-down: claude's 3 aliases ARE its whole catalogue and the `mais…` button never appears, while opencode's 478 across 6 providers page 6 at a time.

**Harness is chosen once, at `/new` — it is not a per-session knob.** *Revised 2026-07-23 (Lucas).* The first cut offered a harness switch on a live session, mapped to "arm it, and the next turn opens a fresh session there". That was answering a question nobody asked: switching only means something if the context comes along, and it cannot. `opencode` has `export <sessionID>` / `import <file>`, `claude` has no counterpart at all — so claude→opencode would mean rewriting a transcript into opencode's JSON schema, and the return trip is impossible. A lineage therefore belongs to its harness for life (AD-3), and the session panel offers only **model** and **effort**.
Harness lives in the `/new` scope, alongside the model and effort a fresh session inherits.

**Two scopes, one panel.** Knobs are addressed by *scope*: a session id, or the sentinel `registry.NEW` for the session `/new` is about to create. `NEW` reads and writes the `defaults` block, which every finished turn overwrites — so a new session starts on the last interaction's harness/model/effort. The panel code is scope-agnostic; only `registry` knows there are two stores.
`/new --backend X` writes the same `NEW` knob the button does, so typing it and tapping it are the same act on the same state.

**Vocabulary.** `harness` = the CLI (claude, opencode). `provider` = who supplies the key (nvidia, openrouter, google) — the sense opencode itself uses, and the level the model drill-down groups by.
Calling the harness a "provider" (the first cut did) collides with that. Button labels stay English (`harness` · `model` · `effort`), matching `BUILD`/`PLAN`, which were already English.

**Panel taps spend no callback_data on the session id.** The panel always edits the anchor message, and `reply_map` already resolves that message_id → session_id, leaving all 64 bytes for values. `p:s:m:openrouter/qwen/qwen3-coder-next` fits with room to spare.

### AD-16 — Model labels: qualify by provider, compress only on overflow
The same model name appears under several providers — Lucas's own 30-day history has `glm-5.2` under `nvidia/`, `openrouter/`, `opencode/` and `ollama-cloud/`. An unqualified shortlist would therefore show two buttons reading `glm-5.2` that do different things. So a model button is `<provider>·<model>`, with two-letter provider abbreviations (`opencode`/`openrouter` share a four-letter prefix, so the map is chosen data, not a mechanical prefix).

The budget is about twelve characters. `frontend/select/labels.py` spends it progressively, and **a name that already fits is never touched** — an abbreviation you have to decode costs more than a long name you can read:

1. separators out, **including the version dot** → `glm-5.2` → `glm52`, `kimi-k2.6` → `kimik26` (Lucas: "I'll know that 52 means 5.2" — it also stops `or·glm5.2` carrying two dots that mean different things)
2. noise tokens dropped (`latest`, `instruct`, `preview`, `chat`)
3. alpha tokens contracted to two letters, digit-bearing tokens kept whole → `deepseek-v4-flash` → `dev4fl`
4. hard cut

Contraction sits before truncation because it preserves distinctions: `qwen3-coder` and `qwen3-coder-next` truncate to the same nine characters but contract to `qwen3co` / `qwen3cone`.
The vendor namespace (`deepseek-ai/`) is dropped entirely — the provider prefix already says it.
Inside one provider's own page the prefix is dropped too, since every row would repeat it.

`config.json` `model_aliases` overrides any id by hand. The rule gives `nv·dev4fl`; Lucas reads that name daily and prefers `nv·dsv4f`, which is a preference no algorithm should be guessing.

### AD-17 — The shortlist is read from usage, not curated
`catalog.favourites()` ranks the last 30 days of opencode sessions by count, ties broken by recency, intersected with the configured catalogue (a model whose provider vanished stops being offered rather than failing at dispatch). The curated "cheap and good" guess it replaced was wrong by a wide margin: it offered models used once each while the real top three had 91, 42 and 15 sessions. A machine with no history falls back to the cheap levels.

The source is one query over `session.model` + `time_updated`, which opencode indexes anyway.
