---
description: Map the state of the art of a field — fill refs/REFS.md plus one review yaml per kept paper, and emit a ≤200-line summary written to support a decision (not a related-work section).
args: <field> [refs dir]
type: research-brief
confirm: plan
agents: researcher, verifier
uses:
---

Map the state of the art for: $@

This is an execution request, not a request to explain or implement the workflow instructions.
Execute the workflow. Do not restate the protocol. Your first tool calls create directories and write the plan artifact.

## Scope — read before running

`sota` maps **a field**, not "anything deep". If the request is a narrow "what is X" explainer, a single claim, or a document to digest, this is the wrong flow — use `literature`, `compare`, or `summarize`. The question `sota` answers is *"where does this field stand, and what does that imply for a decision we are about to make?"*

It produces **two artifacts for two different readers**, and both are required:
- **machine-facing** — `refs/REFS.md` lines plus one `refs/<key>.yaml` review per kept paper.
  Later flows read these; this is what makes the next pass over a neighbouring field cheap.
- **human-facing** — a summary written to support a decision, capped at Step 5's number. Not a related-work section, not an exhaustive brief. Lucas reads it; the yaml holds the rest.

The artifact is the memory. A run that leaves only a chat answer produced nothing.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Web: `core/tools/web/search` (flags `--type neural|keyword`, `--since`, `--domains`, `--content`)
- Academia: `core/tools/paper/papers` (`--ss` reports `venue` + `peer_reviewed`; `--reviewed` drops preprints; `--min-cit N` drops noise). **It answers `{"error": ...}` and exits 1 when the service is down — check with `core/run tools/wos/deps --feature latex` before trusting an empty result.**
  Both arms were dead on 2026-09-13; the run that proved the way through reached every source with
  `core/tools/web/search` targeted at venue hosts, which keeps the peer-review discipline but makes
  `venue` and `citations` something you establish per page rather than read off a field.
- Repos: `core/tools/web/code-search`
- Fetch a URL: `core/tools/web/fetch`
- Agent delegation: use `subagent` when available
- On `Tool not found`: map to the canonical visible tool or record the capability as blocked.
  Never invent a tool name, never silently skip the step.

Avoid crash-prone PDF parsing. Prefer paper metadata, abstracts, HTML, official docs. If only a PDF exists, cite the PDF URL from search metadata and mark full-text parsing as blocked.

## Required Artifacts

Derive a short name from the field: lowercase, hyphenated, no filler, at most 5 words.

Every run must leave on disk:
- `outputs/.plans/<name>.md` — the plan
- `<refs dir>/REFS.md` — level-tagged reference lines, appended
- `<refs dir>/<key>.yaml` — one review per kept paper
- `outputs/<name>-sota.md` — the ≤200-line decision summary
- `outputs/<name>-sota.provenance.md` — the provenance file

`<refs dir>` is the target project's `refs/` when the field serves a project, or `core/refs/` for workspace-level work. If not given, ask which one in Step 1 — refs with no home are lost work.

After plan approval, never end with chat-only output. If a capability fails, continue degraded and still write the summary and provenance file with `Verification: BLOCKED`.

## Step 1 — Plan

Write `outputs/.plans/<name>.md` immediately. It must state:
- **the decision this map serves** (one paragraph — if there is none, say so; the summary is then written for the next reader who will have one)
- the field's boundaries: what is in, what is deliberately out
- key questions and the evidence that would answer them
- the target `<refs dir>`
- the scale decision (below), made before owners are assigned
- a task list, a verification log, and a decision log

Then stop, summarize briefly, and ask:

`Proceed with this SOTA map? Reply "yes" to continue, or tell me what to change.`

Gather nothing until confirmed. On requested changes, rewrite the plan file, then ask again.

## Step 2 — Scale

Direct (lead-owned, no subagents): a field small enough to cover in 3–10 tool calls, or one you already hold refs for and are refreshing.

Decomposed — spawn `researcher` subagents only when it clearly helps:
- two or three competing approaches to contrast → 2 subagents
- a broad field with distinct sub-areas → 3–4 subagents
- multi-domain field (e.g. method + benchmark + deployment) → 4–6 subagents

Keep subagent task JSON small and valid; no multi-paragraph instructions inside it; always `failFast: false`; do not name tools that are not visible in the current tool set.

```json
{
  "tasks": [
    { "agent": "researcher", "task": "Read outputs/.plans/<name>-T1.md and write <name>-sota-T1.md.", "output": "<name>-sota-T1.md" },
    { "agent": "researcher", "task": "Read outputs/.plans/<name>-T2.md and write <name>-sota-T2.md.", "output": "<name>-sota-T2.md" }
  ],
  "concurrency": 4,
  "failFast": false
}
```

## Step 3 — Gather in refined rounds

Run **at least two rounds**. Round 1 is broad; let its findings sharpen Round 2 — never fire all queries at once. Reach academia, web, and repos each round.

**Source-level discipline is mandatory** (full rule:
[`core/refs/CONTEXT.md`](../../refs/CONTEXT.md)). arXiv is the easiest surface, so an unguarded pass returns almost only preprints, which are **not peer reviewed**. Every round must also reach published venues (ACL/EMNLP anthology, ACM DL, IEEE, OpenReview with an accepted venue). Prefer the published URL over the arXiv one when both exist. **A round that yields only `[P]` is incomplete** — say so and re-run before concluding.

**Iteration cap:** at most **4** rounds. Exit early when a round adds no new work you would keep (saturation). On hitting the cap without saturation, stop and record the field as under-covered in the summary — do not loop further.

## Step 4 — Capture references (machine-facing artifact)

For **every kept source**, append one line to `<refs dir>/REFS.md`: level marker `[A] [B] [P] [V] [C]`, title, canonical URL, and a short "why it matters to us".

For every source you would **cite or reason from**, also write `<refs dir>/<key>.yaml` using the workspace review schema (`key`, `type`, `year`, `venue`, `url`, `citations`, `contributions`, `gaps`, `tags`, `relevance`, `notes`) — see the target `refs/CONTEXT.md` for the domain tag vocabulary, and put role tags (`foundational` · `survey` · `competing-work` · `baseline` · `ground-truth` · `method-source` · `tool` · `application`) first. Read the source before writing its yaml; a review written from a title is a fabrication.

Skim-only hits stay as REFS.md lines and get no yaml. Say in the summary how many of each.

## Step 5 — Write the ≤200-line decision summary (human-facing artifact)

Write `outputs/<name>-sota.md`. **Hard cap: 200 lines**, and this is the one place it is declared —
it is what Lucas will read in one sitting, not the file-shape law in `core/hooks/limits.env`, which no reader of this flow consults. If it does not fit, cut — the yaml holds the detail. Structure:

1. **Verdict** — 3–8 lines. Where the field actually stands, and what that means for the decision named in the plan. Lead with the answer.
2. **The live positions** — the small number of real approaches, one short block each: what it claims, its strongest evidence with level, its known failure mode.
3. **Consensus vs contested** — what is settled and what is still argued. Cite levels; a `[P]`-only position is contested by construction.
4. **What this implies for us** — the decision-relevant part. Options with trade-offs, not a recommendation dressed as a fact. Name what would change your mind.
5. **Gaps** — what nobody has done. This is where our own contribution would sit.
6. **Refs** — pointer to `<refs dir>/REFS.md` and the yaml files written. Not a bibliography.

State the evidence caveat once for the whole summary: where a conclusion leans on preprint-only evidence, mark it, and never let a `[P]` alone gate a workspace or project policy change.

## Step 6 — Verify

If subagents were used, run the `verifier` agent against the summary before delivery; do not run `verifier` and `reviewer` in the same parallel call. For direct-mode runs, verify yourself:
confirm each URL resolves, each level marker matches the venue, and each yaml's `relevance` is filled. Record findings in the provenance file as FATAL / MAJOR / MINOR. Fix FATAL before delivering; note MAJOR under Gaps; accept MINOR.

Prove applied fixes on disk with grep/diff/stat — never claim a fix landed on the strength of having written it.

## Step 7 — Deliver

Write `outputs/<name>-sota.provenance.md`:

```markdown
# Provenance: [field]

- **Date:** [date]
- **Decision served:** [one line, or "none stated"]
- **Rounds:** [n of max 4] · saturated: [yes/no]
- **Sources consulted / accepted / rejected:** [counts]
- **Level mix:** [A]=n [B]=n [P]=n [V]=n [C]=n
- **Reviews written:** [list of <key>.yaml]
- **Verification:** [PASS / PASS WITH NOTES / BLOCKED]
- **Plan:** outputs/.plans/<name>.md
```

Before responding, verify every required artifact exists on disk and that the summary is ≤200 lines (`wc -l`). Final chat response is brief: link the summary, the refs file, the yaml count, and any blocked checks.

## Integrity

Read before you summarize — a URL you did not open is not a source. Every claim, number, or benchmark maps to a source URL or a research note. Mark inferred vs verified honestly. No invented sources, venues, levels, numbers, or figures.
