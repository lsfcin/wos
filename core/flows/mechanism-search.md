---
description: Systematic search for social mechanisms (individual motive → collective effect) against a quantified ralo — forced-diversity generation, deliberative human filter, output ready for a test-to-kill pilot.
args: <ralo>
type: domain
confirm: plan
agents: researcher, writer
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Paper search: use available paper-search tools or `alpha` via `bash`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

# mechanism-search
> Systematic search for social mechanisms (Waze-style: individual motive → collective effect)
> against a quantified drain of money or attention — forced-diversity generation, deliberative human
> filter, output ready for a test-to-kill pilot.

**`ralo`** — literally a drain — is the instituto program's word for a quantified flow of money or
attention leaving the people who produce it. It is kept in Portuguese here because it names the
program's own files (`branches/instituto/RALOS.md`) and its inventory of them.

Parent program: `branches/instituto/MOTOR.md` (read first — pitfalls and fundamentals). Fundamentals:
LLMs = novelty at volume, humans = feasibility, pilot = truth (Si et al. 2024, arXiv 2409.04109;
ideation-execution gap, arXiv 2506.20803).

## Input

One quantified `ralo` (from `branches/instituto/RALOS.md` or laplata): flow in R$/month, who loses,
who captures, the capture mechanism.

## Required artifacts

Derive a short name from the `ralo` (lowercase, hyphens, ≤5 words). Every round must leave on disk:

- `outputs/.plans/<name>.md` — plan plus the queue-rule check
- `outputs/.drafts/<name>-gen-{1,2,3}.md` — candidates per persona
- `outputs/<name>-familias.md` — deduplicated families (the human filter's material)
- survivors appended to `branches/instituto/ROADMAP.md` (only after the human filter)

Once generation starts, never end chat-only. If a capability fails, continue in degraded mode and
record the blockage in the plan.

## Plan (stop for confirmation)

Before any generation:
1. **Queue rule** — check `branches/instituto/ROADMAP.md`: do not generate again while 2 candidates
   are waiting on a pilot. If the queue is full, stop and report.
2. **Corpus check** (`researcher`) — retrieve the 5-8 precedents closest to the `ralo` from the
   corpus (`academy/papers/mechanism-search/refs/`). If the corpus is empty: run `/research lit`
   first (stage 0).
3. Write `outputs/.plans/<name>.md` (ralo, precedents, chosen personas, list). Summarize and ask
   for explicit confirmation before spawning generators.

## Agents and sequence

1. **Divergent generation** (3× `researcher` in parallel, antagonistic personas — e.g. behavioural
   economist, community organizer, crypto incentive engineer) — each generates 8-12 candidates into
   `outputs/.drafts/<name>-gen-N.md`. Mandatory anti-collapse techniques:
   - precedent mutation (take a mechanism from the corpus, swap 1 dimension: population, trigger,
     currency, scale)
   - distant analogy (biology, games, religion, logistics)
   - pure-exploration quota: ≥20% with no precedent at all
2. **Candidate format** (mandatory, 6 lines): ralo · individual motive (why a person uses it WITHOUT
   altruism) · collective effect · who operates it · why it does not exist yet · test-to-kill sketch
   ≤3 months.
3. **Dedup and grouping** (`writer`) — merge near-duplicates, group by mechanism family into
   `outputs/<name>-familias.md`. NEVER rank by LLM as the final filter (self-evaluation is not
   trustworthy).
4. **Deliberative human filter** — Habermas format: present families to the group (board/class),
   collect individual positions, synthesize a group statement, iterate 1×. Output: 2-3 survivors
   with a named owner.
5. **Handoff** — each survivor becomes an entry in the program's ROADMAP with a detailed
   test-to-kill.

## Integrity

- A cited precedent must exist in the corpus or come with a source URL — never invent a precedent, a
  flow figure or a pilot result.
- The final filter is human; LLM output is always a proposal, never a decision.

## Output

`branches/instituto/` — surviving candidates appended to ROADMAP.md; the post-mortem of a killed
pilot goes to the cluster's archive or to a paper. New knowledge with a source → RALOS.md.
