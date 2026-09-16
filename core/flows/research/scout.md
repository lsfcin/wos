---
description: Scout a topic across web + repos + academia in refined rounds, then convert the findings into a model-tiered, impact-flagged action plan written into the target project's ROADMAP. For "research X, then tell me what we should do about it in our own system".
args: <topic> [target ROADMAP path]
type: domain
confirm: plan
agents: researcher
uses: sota
---

Scout and plan for: $@

This is an execution request. Do not explain the protocol — run it.

## Tool Discipline (read first)

Tool names are literal; use only tools visible in the current tool set. Gathering tools:
`core/tools/web/search` (web), `core/tools/web/code-search` (repos), `core/tools/paper/papers` (academia,
`--ss`/`--reviewed`/`--min-cit` for venue filtering), `core/tools/web/fetch` (URL). If a tool
returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.
A tool that RUNS and answers `{"error": ...}` is the other failure and is not the same thing:
`papers` was dead on both arms on 2026-09-13, so check with `core/run tools/wos/deps --feature
latex` before reading an empty result as "the field is quiet", and route through
`core/tools/web/search` aimed at venue hosts when it is down.

## Required Artifacts

Every run must leave three things on disk before the final response:
- everything `sota` requires — level-tagged lines in the relevant `refs/REFS.md`, one review
  yaml per kept paper, and the ≤200-line SOTA summary (Step 2);
- the plan written into the target ROADMAP (Step 5).

Never end chat-only after Step 2 begins. If gathering is blocked, write a partial plan marked
`BLOCKED` and say what failed. Read every source before summarizing it; never invent sources,
venues, levels, or results.

## Composition — `scout = sota + map-to-our-system + tiered plan`

`scout` **uses** [`sota`](sota.md) for its whole gathering half. That is a declared edge
(`uses: sota` in the frontmatter), not a suggestion: do not reimplement search, level discipline,
or reference capture here — run `sota` and build on its artifacts.

Keep both entrypoints straight:

| You want | Run |
|----------|-----|
| the field map, no plan | `sota` |
| the field map **and** what we should do about it | `scout` |
| a brief on a topic that is not a whole field | `literature`, `compare`, `summarize` |

The distinctive part of `scout` is the back half — map-to-system → tiered plan → ROADMAP.

## Step 1 — Frame

Write a one-paragraph frame: what decision this scouting serves, and which project/ROADMAP the
plan will land in. If the target ROADMAP is not given, ask which one (a plan with no home is a
violation of the workspace "plans live in roadmaps" rule).

## Step 2 — Gather: run `sota`

Run [`sota`](sota.md) on the topic, with `<refs dir>` = the target project's `refs/` (or
`core/refs/` for workspace-level work). `sota` owns the whole gathering half: refined rounds
across web/repos/academia, the mandatory source-level discipline, the round cap, the level-tagged
`REFS.md` lines, the per-paper review yamls, and the ≤200-line summary. Do not restate those
rules here and do not run your own parallel search.

Two adjustments when `sota` runs under `scout`:
- **Skip its plan confirmation.** The user already confirmed at Step 1 of this flow; a second
  gate on the same work is noise. Pass the Step 1 frame as `sota`'s "decision this map serves".
- **Its summary is an input, not the deliverable.** Read `outputs/<name>-sota.md` and the yamls
  yourself before Step 3 — the mapping is synthesis, and synthesis is never delegated.

If `sota` finishes under-covered (cap hit without saturation, or a `[P]`-only round it could not
fix), carry that caveat forward — it constrains how hard the plan may lean on those findings.

## Step 3 — Map to our system

Read the actual state of the target project (its CONTEXT.md, ROADMAP, relevant code/docs).
For each finding, state plainly: does it **confirm** what we do, **contradict** it, or reveal a
**gap**? Cite the source level for each claim. Contradictions and gaps become plan items;
confirmations become a short "we are already aligned on X" note (equally valuable — it stops us
re-solving solved problems).

## Step 4 — Write the tiered, flagged plan into the ROADMAP

Organize the plan as **frentes** (fronts), each a self-contained line of work with numbered
steps. Every step carries three things:

- **impact flag** — 🔴 `decide-first` (changes shared policy or touches security; needs Lucas's
  sign-off + more evidence before coding — usually with an open question), 🟡 `pilot-first`
  (prove on one folder, measure, then generalize), 🟢 `safe` (mechanical/additive, low blast
  radius). A frente that changes workspace-wide behavior **opens** with a 🔴 step.
- **model level** — the *floor* level that suffices: `haiku` (mechanical), `sonnet` (normal
  engineering/writing), `opus` (design, security, cross-cutting judgment). Bigger always works,
  it just costs more.
- **switch mechanism** — how that level gets onto that step (see the canonical guide below).

State the **evidence caveat once** for the whole plan: where a step leans on preprint-only
evidence, mark it and keep it 🔴/🟡 — a preprint never becomes a hard gate on its own.

End the plan with a **sequencing** section ordered by (impact × cheapness) ÷ risk, and note
that the 🔴 steps are the discussions to have before any code.

## Canonical model-switching guide (reusable — reference this, do not re-tabulate per plan)

| Mechanism | When to use | Who acts |
|-----------|-------------|----------|
| **Same session, `/model`** | The next whole chunk needs a different level. Cheapest for a sustained stretch at one level. | **User** flips it; an agent cannot change its own session model. |
| **`/craft` autorouting** | A codeable feature with mixed-level steps. The loop plan assigns craft-low(haiku)/medium(sonnet)/high(opus) per step; no manual switch. | The flow spawns the right level per loop. |
| **Agent tool `model:` override** | One sub-task needs a different level than the driver — especially eval, where the graded model must be the weak one. | The driving agent spawns a sonnet/haiku subagent inline; no session change. |
| **Handoff (`/handoff`)** | A clean level boundary + heavy context: finish the design phase at one level, start a fresh session at another carrying only the resume prompt. | **User** starts the new session at the chosen model. |

**Default mapping:** 🔴 decide-first steps → **Opus, same session** (judgment about shared
behavior). 🟢/🟡 build steps → **Sonnet via `/craft`** (mechanical parts drop to haiku
automatically). Run **haiku deliberately** only where a weak model is the *subject under test*
(e.g. behavioral eval gold tasks), spawned via the Agent-tool override.

## Step 5 — Confirm before writing

Summarize the frentes briefly and ask:

`Write this plan into <ROADMAP path>? Reply "yes", or tell me what to change.`

Only after confirmation: write the plan into the ROADMAP (inline or as a referenced sub-roadmap
file), link it from the project's goal/CONTEXT, and confirm the refs are captured. Keep the
final chat response brief: link the ROADMAP, the refs file, and flag the 🔴 steps that need
discussion.
