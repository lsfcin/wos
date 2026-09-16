---
description: Compare multiple sources on a topic and produce a source-grounded matrix of agreements, disagreements, and confidence.
args: <topic>
type: research-brief
confirm: none
agents: researcher, verifier
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Compare sources for: $@

This is an execution request, not a request to explain the workflow. Your first actions should be tool calls that write
the plan artifact.

Derive a short name from the comparison topic (lowercase, hyphens, no filler words, ≤5 words). Use this short name for
all
files in this run.

## Required Artifacts

Every run must leave these on disk:
- `outputs/.plans/<name>.md`
- `outputs/<name>-comparison.md`
- `outputs/<name>.provenance.md`

Once evidence gathering starts, never end with chat-only output. If a capability fails, continue in degraded mode and
still write a partial matrix plus provenance with `Verification: BLOCKED`.

## Step 1: Plan

Write the comparison plan to `outputs/.plans/<name>.md`: which sources to compare, which dimensions to evaluate,
expected output structure. `confirm: none` — summarize the plan to the user in one or two lines and continue immediately
(do not wait for approval).

## Step 2: Scale

- **2 sources, narrow:** compare them directly (lead-owned), no subagents.
- **3+ sources or a broad set:** spawn one `researcher` subagent per source cluster to gather material in parallel.
Do not inflate a two-source comparison into a multi-agent survey. State the decision in the plan before assigning
owners.

## Step 3: Build the matrix

Comparison matrix covering: source, key claim, evidence type, caveats, confidence. Distinguish agreement, disagreement,
and uncertainty clearly. Generate charts when the comparison involves quantitative metrics; use Mermaid for
method/architecture comparisons. Save to `outputs/<name>-comparison.md`.

Integrity: read each source before characterizing it; URL or it didn't happen; mark inferred vs directly-stated claims;
never invent sources, numbers, or figures.

## Step 4: Cite + deliver

For broad runs, run the `verifier` subagent to verify source URLs and add inline citations to the matrix. For direct
2-source runs, verify URLs and add citations yourself. End the matrix with a `Sources` section of direct URLs.

Write provenance to `outputs/<name>.provenance.md`:

```markdown
# Provenance: [topic]
- **Date:** [date]
- **Sources compared:** [count / list]
- **Sources accepted / rejected:** [...]
- **Verification:** [PASS / PASS WITH NOTES / BLOCKED]
- **Plan:** outputs/.plans/<name>.md
```

Before responding, verify on disk that all required artifacts exist. Final response is brief: link the matrix +
provenance, note any blocked checks.
