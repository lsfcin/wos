---
description: Run a literature review on a topic using paper search and primary-source synthesis.
args: <topic>
type: research-brief
confirm: none
agents: researcher, verifier, reviewer
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Paper search: use available paper-search tools or `alpha` via `bash`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Investigate the following topic as a literature review: $@

Derive a short name from the topic (lowercase, hyphens, no filler words, ≤5 words). Use this short name for all files in this run.

## Required Artifacts

Every run must leave these on disk:
- `outputs/.plans/<name>.md`
- `outputs/.drafts/<name>-research-*.md`
- `outputs/<name>.md`
- `outputs/<name>.provenance.md`

Once evidence gathering starts, never end with chat-only output. If a capability fails, continue in degraded mode and still write a partial review plus provenance with `Verification: BLOCKED`.

## Workflow

1. **Plan** — Outline the scope: key questions, source types to search (papers, web, repos), time period, expected sections, and a small task list plus verification log. Write the plan to `outputs/.plans/<name>.md`. Briefly summarize the plan to the user and continue immediately. Do not ask for confirmation or wait for a proceed response unless the user explicitly requested plan review.
   - When updating the plan list later, keep edits small and valid. If an edit fails, rewrite the full corrected plan
     file then continue.
2. **Gather** — Use the `researcher` subagent when the sweep is wide enough to benefit from delegated paper triage before synthesis. For narrow topics, search directly. Researcher outputs go to `<name>-research-*.md`. Do not silently skip assigned questions; mark them `done`, `blocked`, or `superseded`.
3. **Synthesize** — Separate consensus, disagreements, and open questions. When useful, propose concrete next experiments or follow-up reading. Generate charts for quantitative comparisons across papers and Mermaid diagrams for taxonomies or method pipelines. Before finishing the draft, sweep every strong claim against the verification log and downgrade anything that is inferred or single-source critical.
4. **Cite** — Spawn the `verifier` agent to add inline citations and verify every source URL in the draft.
5. **Verify** — Spawn the `reviewer` agent to check the cited draft for unsupported claims, logical gaps, zombie sections, and single-source critical findings. Fix FATAL issues before delivering. Note MAJOR issues in Open Questions. If FATAL issues were found, run one more verification pass after the fixes.
6. **Deliver** — Save the final literature review to `outputs/<name>.md`. Write a provenance record alongside it as `outputs/<name>.provenance.md` listing: date, sources consulted vs. accepted vs. rejected, verification status, and intermediate research files used. Before you stop, verify on disk that both files exist.
