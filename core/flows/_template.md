---
description: One line — what durable artifact this flow produces.
args: <topic>
type: research-brief
confirm: none
agents: researcher, verifier
uses:
---
<!--
Flow template — and the canonical wording of the five disciplines.

This file is a template, nothing more: it holds no special status and is not a validator
oracle (see core/SCHEMA.md). Its one privilege is being the place the
discipline wording is *kept*, so flows copy from one source instead of drifting apart.

To write a flow: copy this file, fill the frontmatter per core/SCHEMA.md, then keep the
discipline blocks your `type` requires and delete the rest. Each block below is annotated
with the types that require it:

  discipline           research-brief   utility   domain
  tool-discipline           req           req      req
  required-artifacts        req           rec      req
  provenance                req            —       rec
  scale-gate                req           rec      rec
  integrity                 req           req      req

`uses:` is a comma list of other flows this one invokes; leave it empty for a leaf flow.
The `uses:` graph must stay a DAG — a flow may never, directly or transitively, use itself.
Execution loops are a different thing and are allowed; see the runtime-cap block below.
-->

## Tool Discipline (Read First)
<!-- required: research-brief · utility · domain -->

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for
runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Paper search: use available paper-search tools or `alpha` via `bash`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability
  as blocked. Never invent a tool name and never silently skip the step.

Run this flow for: $@

This is an execution request, not a request to explain or implement the workflow instructions.
Execute the workflow. Do not answer by describing the protocol, do not explain these
instructions, and do not restate the protocol. Your first actions should be tool calls that
create directories and write the plan artifact.

## Required Artifacts
<!-- required: research-brief · domain — recommended: utility -->

Derive a short name from the topic: lowercase, hyphenated, no filler words, at most 5 words.
Use it for every file this run writes.

Every run must leave these files on disk:
- `outputs/.plans/<name>.md`
- `outputs/<name>.md`
- `outputs/<name>.provenance.md`   <!-- provenance discipline only -->

Once work starts, never end with chat-only output. If a capability fails, continue in degraded
mode and still write a partial artifact, marked `Verification: BLOCKED`.

## Plan
<!-- part of required-artifacts -->

Write the plan to `outputs/.plans/<name>.md` before doing any work. State the scale decision in
the plan before assigning owners.

- `confirm: plan` → stop here, summarize the plan briefly, and ask:
  `Proceed with this plan? Reply "yes" to continue, or tell me what to change.`
  Gather nothing until the user confirms. If they ask for changes, rewrite the plan file first,
  then ask again.
- `confirm: none` → summarize the plan in one short paragraph and continue.

## Scale Gate
<!-- required: research-brief — recommended: utility · domain -->

Decide direct-vs-decomposed explicitly, and record the decision in the plan.

Direct (lead-owned, no subagents):
- a single fact or narrow question, including any "what is X" explainer
- anything answerable in 3–10 tool calls

For "what is X" topics you MUST NOT spawn subagents unless the user explicitly asks for
comprehensive coverage, current landscape, benchmarks, or production deployment. Do not inflate
a simple explainer into a multi-agent survey.

Decomposed (spawn `researcher` subagents) only when decomposition clearly helps:
- direct comparison of 2–3 items → 2 subagents
- broad survey or multi-faceted topic → 3–4 subagents
- complex multi-domain research → 4–6 subagents

## Execution Loops
<!-- optional: any type that retries a step -->

A flow may return to an earlier step when a check fails — that is iteration, not a cycle, as long
as state changes each pass. Any such loop must declare both guards, or it is a hang:
- an **exit condition** (what "good enough" means), and
- an **iteration cap** — a hard maximum number of passes, stated as a number.

On hitting the cap, stop and deliver the best artifact so far with the failure recorded. Never
loop unbounded, and never loop on a step whose inputs did not change.

## Execute → Deliver

Do the work and write the artifact. Delegate gathering; never delegate synthesis — write the
final artifact yourself.

## Provenance
<!-- required: research-brief — recommended: domain — not required: utility -->

Write a sidecar next to the artifact as `<name>.provenance.md` (a flow may instead declare a
single running log, as long as it is declared):

```markdown
# Provenance: [topic]

- **Date:** [date]
- **Rounds:** [number of rounds]
- **Sources consulted:** [count and/or list]
- **Sources accepted:** [count and/or list]
- **Sources rejected:** [dead, unverifiable, or removed]
- **Verification:** [PASS / PASS WITH NOTES / BLOCKED]
- **Plan:** outputs/.plans/<name>.md
- **Research files:** [files used]
```

## Integrity
<!-- required: research-brief · utility · domain -->

- Read before you summarize. A URL you did not open is not a source.
- URL or it didn't happen — every critical claim, number, figure, table, or benchmark maps to a
  source URL, research note, artifact path, or command output.
- Mark inferred vs verified honestly; downgrade or remove unsupported claims.
- No invented sources, numbers, figures, benchmarks, images, charts, or tables.
- Before the final response, verify on disk that every required artifact exists. Prove applied
  fixes with grep/diff/stat — do not claim a fix landed on the strength of having written it.
