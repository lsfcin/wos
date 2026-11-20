---
description: Turn research findings into a polished paper-style draft with equations, sections, and explicit claims.
args: <topic>
type: research-brief
confirm: none
agents: writer, verifier
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Write a paper-style draft for: $@

Derive a short name from the topic (lowercase, hyphens, no filler words, ≤5 words). Use this short name for all files in this run.

## Required Artifacts

Every run must leave these on disk:
- `outputs/.plans/<name>.md`
- `papers/<name>.md`
- `papers/<name>.provenance.md`

Once drafting starts, never end with chat-only output. If source material is missing, leave labeled placeholders rather than inventing results, and record the gap in provenance.

Requirements:
- Before writing, outline the draft structure: proposed title, sections, key claims to make, source material to draw from, and a verification log for the critical claims, figures, and calculations. Write the outline to `outputs/.plans/<name>.md`. Briefly summarize the outline to the user and continue immediately. Do not ask for confirmation or wait for a proceed response unless the user explicitly requested outline review.
- Use the `writer` subagent when the draft should be produced from already-collected notes, then use the `verifier` subagent to add inline citations and verify sources.
- Include at minimum: title, abstract, problem statement, related work, method or synthesis, evidence or experiments, limitations, conclusion.
- Use clean Markdown with LaTeX where equations materially help.
- Follow the system prompt's provenance rules for all results, figures, charts, images, tables, benchmarks, and quantitative comparisons. If evidence is missing, leave a placeholder or proposed experimental plan instead of claiming an outcome.
- Generate charts only for source-backed quantitative data, benchmarks, and comparisons. Use Mermaid for architectures and pipelines only when the structure is supported by sources. Every figure needs a provenance-bearing caption.
- Before delivery, sweep the draft for any claim that sounds stronger than its support. Mark tentative results as tentative and remove unsupported numerics instead of letting the verifier discover them later.
- Save exactly one draft to `papers/<name>.md`.
- End with a `Sources` appendix with direct URLs for all primary references, and write `papers/<name>.provenance.md` (date, source material used, verification status of claims/figures). Verify both files exist on disk before responding.
