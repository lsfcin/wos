---
description: Looped engineering flow — development in file-relayed loops with model autorouting; each loop runs in a fresh, cheap session that reads exactly one file.
args: <task or feature request>
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.
- Agent delegation: use `subagent` / `Agent` when available; otherwise the user opens a fresh session per loop.
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Engineer this task in loops: $@

Execute, do not explain. Derive a feature short name (lowercase, hyphens, ≤5 words), and ask for no
confirmation beyond the Loop 0 interview.

> **This is the `feature` folder of the craft tree** ([`route.md`](route.md), [`tree.md`](tree.md)). Reach it via the
> router, which pins `subtree: feature`. It is **contract-first**: Loop 0 sets a supervision panel, Loop 3.5 lays out
> every module/step I/O contract before any code, Loop 3 runs a recurrent concept-symmetry review. Research and
> architecture-decision tasks belong to other folders.

## Core Principle — Files, Not Conversation

Each loop is executed by a **fresh session** of the cheapest capable model. That session receives only:

1. Its own loop section from this flow file.
2. **One** input file: the previous loop's output (which embeds the Carry block — see below).

It never receives conversation history. It appends its output to its own loop file and returns a **one-line verdict** to
the orchestrator. The orchestrator never reads loop file contents — only verdicts. This is how the flow *saves* tokens
instead of spending them: N cheap short sessions instead of one long expensive one.

### File protocol

- Directory: `<project>/.craft/<feature-name>/` inside the target project's own repo.
- Files: `0-clarify.md`, `1-plan.md`, `2-ground.md`, `3-arch.md`, `3b-contracts.md` (feature folder), `4a-tests.md`,
  `4b-code.md`, `5-user.md`, `6-ship.md`.
- **Append-only.** Executors add sections; never rewrite prior content. Corrections are new appended sections.
- **Executor self-report.** Every appended section ends with `executor: <agent-type> model=<provider/model-id>
  level=<level> deleg=<none|from→to>` — after a run, `grep executor .craft/<name>/*.md` audits whether routing actually
  happened *and* which provider paid for each loop. The `model=` field MUST include the provider prefix (e.g.
  `model=nvidia/z-ai/glm-5.2`, not bare `model=glm-5.2`) so the per-provider cost split is recoverable from the chain
  alone, without the session log.
- **Small.** Soft cap ~80 lines per file. A loop file that wants to exceed the cap is a smell: the task is too big —
  raise `FLAG: RETURN loop=1 reason=split-needed`. **Declared here and nowhere else, deliberately**: this is a budget
  for what ONE fresh session should be handed, not the file-shape law in `core/hooks/limits.env` — no gate reads it and
  no instrument measures it, so a row over there would be a number with no reader.
- **Carry block.** Every loop file starts with a `## Carry` block **copied verbatim** from the previous file (Loop 0
  creates it). It holds: short name, branch, project root, test command, criticality, acceptance-criteria
  digest, context pointers (project `CONTEXT.md`/`AGENTS.md` paths). This is what makes "read exactly one
  file" true — no loop ever chases earlier files.
- `.craft/` is committed on the feature branch during the flow (audit trail, survives crashes). Loop 6 folds the durable
  outcome into the project's `ROADMAP.md` (workspace policy: plans live in roadmaps) and deletes `.craft/<name>/` in the
  final commit unless Loop 0 recorded `keep-trail: yes`.

### Carry block template

```markdown
## Carry
name: <feature-name> | branch: <branch-name> | root: <project path>
provider: <orchestrator provider, e.g. nvidia | openrouter | opencode | anthropic | copilot> | chain-deleg: <none | deleg=<from>→<to>>
level-map: <one of: nvidia | openrouter | opencode | anthropic | copilot> | verified-on: <date>
test-cmd: <exact command, e.g. `npm test`> | e2e-cmd: <or "none">
criticality: <low|normal|critical> | verdict: <padaria|standard|critico>
subtree: <padaria|feature|research|architecture> | supervision: io-signoff=<yes|no> arch-review=<none|per-feature|periodic> arch-review-supervised=<yes|no>
criteria: <one line per acceptance criterion, numbered C1..Cn>
tasks: <filled by Loop 1 — one line per row: Tn — task — files — level>
context: <paths to project CONTEXT.md / AGENTS.md the executor must read>
```

`provider:` is the orchestrator's chosen provider for the chain. `level-map:` names which per-provider table row (the
per-provider table in [`routing.md`](routing.md)) fills the chain's levels — usually equals `provider`, but for downward
delegation it may differ (e.g. `provider: openrouter` + `level-map: nvidia` means the openrouter orchestrator runs every
loop on nvidia subagents to save credits — see [`routing.md`](routing.md) § Provider delegation). `chain-deleg:` records
the delegation edge if one was applied. ALL THREE fields must be filled — a chain without an explicit provider+map is
undefined and Loop 0 must escalate to the user. The orchestrator runs the `opencode models | awk -F/` check **before**
filling these so the row actually exists in this runtime.

Loops 0–1 may fill TBD Carry fields (branch, test-cmd, tasks); from Loop 2 on the block is frozen and copied verbatim.

## Autorouting

Levels are provider-agnostic. Loop 1 assigns a level + effort **per task row** in the plan; loops without a plan row use
the defaults below.

| Task type | Level | Effort | Escalate to next level when |
|---|---|---|---|
| Loop 0 — clarify interview, criticality gate | high | high | ambition high, or innovation/creativity demanded → max |
| Loop 1 — plan + adversarial plan review | high | high | review leaves ≥1 unresolved FATAL → max |
| Loop 2 — branch + grounding checks | low | low | never (mismatch raises a flag instead) |
| Loop 3 — architecture + evaluation | high | medium | criticality=critical or novel design → max |
| Loop 4a — write failing tests | medium | medium | criterion needs deep domain insight to encode → high |
| Loop 4b — code until green | medium (low for padaria) | medium | 3 consecutive red runs on the same test → high |
| Loop 5 — automated user test | medium | medium | 2 environment/flake failures → high |
| Loop 6 — commit, push, ship notes | low | low | never |

**Escalation rules (general):** escalate exactly one level at a time; append `ESCALATED from=<level> to=<level>
reason=<evidence>` to the current loop file; the escalated session reads the same single input file. If the **max** level
still fails, do not retry — raise a RETURN flag. Never de-escalate mid-loop.

**Max level is never auto-spawned.** Escalation to `max` pauses the flow and surfaces to the user with the evidence line
— max-level quota is scarce and spending it is the user's call. The user either runs that loop in a max-level session or
overrides the escalation.

**Which concrete model fills a level** is in [`routing.md`](routing.md) — the availability check, the per-provider level
maps, the benchmarks, and the downward-only delegation rule. The **orchestrator** reads it once, before Loop 0, to fill
the Carry `provider:` / `level-map:` fields. Executors do not: they are handed a resolved `model=` in the spawn prompt.

## Return Flags

Flag line format, appended at the end of the executor's section:

```
FLAG: RETURN loop=<N> reason=<name> evidence=<one line>
```

- The executor **raises**; the orchestrator **routes**. A return of ≤1 loop backwards is honored automatically.
- Two consecutive returns to the same loop, or any `RETURN loop=0`, stops the flow and goes to the **user** — the intent
  itself is in question.
- The receiving loop re-runs at **one level above** its default (the cheap level already failed to produce a survivable
  artifact).

## Orchestration

The orchestrator (lead session) holds only: short name, current loop, verdicts, flags, and **the provider +
level-map resolved in Loop 0**.

**Routing is structural, not discretionary:** spawn via the pinned executor agent types `craft-low` / `craft-medium` /
`craft-high` (Claude Code: `.claude/agents/craft-*.md`; opencode: `.opencode/agents/craft-*.md`). The pinned executors
pin **one model per runtime**, set in frontmatter (so routing cannot drift inside that runtime). For runtimes that
support per-spawn model override (opencode's `task`/`subagent` literal-a-models), the orchestrator passes the level's
model **from the active provider's row** of [`routing.md`](routing.md), NOT the frontmatter default — the frontmatter
default is just the fallback when the orchestrator doesn't resolve a provider. Spawn each loop with this prompt —
nothing more:

```
Read core/flows/craft/craft.md — the spine, all of it — then the one loop file
that holds your loop: craft-plan.md (0-2), craft-build.md (3-4b), craft-ship.md
(5-6.5). Read no other loop file. Then read
<project>/.craft/<name>/<input-file>. Execute Loop <N>. Append your output to
<project>/.craft/<name>/<output-file> following the embedded template. End your
section with `executor: craft-<level> model=<provider/model-id> level=<level>
deleg=<none|from→to>`. Reply with ONE line:
OK <verdict> | FLAG <flag line> | BLOCKED <reason>.
```

The executor is told its `model=` — it must **not** load `routing.md` to look one up. That is what keeps a loop session
cheap.

**Spawn mechanics are per-runtime and live in [`runtimes.md`](runtimes.md)** — `opencode run` subprocess recipe, Claude
Code `Agent` tool, Copilot CLI, and the portability table. Read only the section for the runtime you are in, once, at
the first spawn.

No runtime `subagent`/`Agent`/`task` tool → the user opens a fresh session per loop with the same prompt and picks the
model per the active level-map; the flow is unchanged.

---

## Cost Gate

- Standard path ≈ 8 short sessions. If the task would take a single medium-level session <30 min end-to-end, it must be
  `padaria` — re-check the gate before proceeding.
- Any loop file hitting the soft cap above → the task is too big; split via `RETURN loop=1 reason=split-needed`.
- The orchestrator context must stay near-empty: verdict lines only. If you find yourself pasting loop file contents
  into the orchestrator, the flow is being run wrong.

Never end a loop with planning-only chat. Never claim the flow is complete unless `6-ship.md` exists on disk with a
commit hash.

## Field Practice (overrides of the Autorouting table)

The bullets below were observed in the `isoroll` post-freeze run (2026-07-14 — 4 chains, 3 shipped same-day) and are
**load-bearing spec, not optional notes**. Each names which Autorouting table row it overrides; conflict between a
bullet and the table → the bullet wins. That is why they stay here and not in [`prior-art.md`](prior-art.md): field
*notes* are history, field *practice* is spec.

| Bullet (below) | Overrides Autorouting row | Effect |
|---|---|---|
| Loop 0 inline when hot | Loop 0 — clarify (high) | Orchestrator can author `0-clarify.md` directly at `max` instead of spawning a craft-high session for the interview |
| Pin branch base in spawn prompt | Loop 2 — branch (implicit, low) | Orchestrator names `base:` non-discretionally when lineage is non-obvious; saves a full plan re-ground |
| Dirty-tree fence | Loop 6 — diff scope | Pre-existing dirty paths listed under `extras: pre-existing-dirty`, not flagged as `RETURN loop=4b reason=dirty-tree` |
| RETURN into high-level → orchestrator-max inline | Escalation rules + max-gate | RETURN to a high-eligible loop → orchestrator amends target file at `max` inline instead of spawning a max executor; only sanctioned structural relaxation |
| Executor death mid-4b → fresh executor continues | Loop 4b escalation clock | Recovery primitive at 4a→4b boundary; red-run clock resets from new ground truth after recovery |

- **Loop 0 inline when context is hot.** If the orchestrator session already holds the user's decisions (approved plan,
  fresh interview), author `0-clarify.md` directly instead of spawning — the interview is the one thing executors can't
  do, and delegation would launder context through a lossy retelling.
- **Pin the branch base in the spawn prompt** when repo lineage is non-obvious (e.g., docs/spec live on an unmerged
  branch, `develop` lacks them). A wrong base costs a full plan re-ground. Correction pattern: append-only `## Plan
  Correction (orchestrator)` section; instruct the next loop that it overrides.
- **Dirty-tree fence.** Pre-existing uncommitted changes in the target repo: name the contaminated paths in every spawn
  prompt from 4b on, and make Loop 6 list them under `extras: pre-existing-dirty` instead of flagging. Never let an
  executor "helpfully" commit or revert them.
- **RETURN into a high-level loop lands on max = the orchestrator.** Don't spawn; rule inline (append `## Amendment` to
  the target loop file with the ruling + sharpened boundaries + re-entry route). Design-wrong is not
  boundary-gap: if the architecture already specifies the missing behavior, don't redesign — sharpen
  boundaries so 4a must cover it, re-run 4a→4b at default levels.
- **Executor death mid-4b (session limit) is cheap to recover**: fresh executor reads 4a + partial 4b, re-runs test-cmd
  for ground truth, continues append-only. Budget hint: 4b is the expensive loop (~150–260k tokens); near a quota
  boundary, hand off at the 4a→4b boundary rather than starting it.
- **Two loops, one repo = worktree fight.** Same-repo loops run sequentially (branch checkouts collide); cross-repo
  loops parallelize freely.
