---
description: Compare a paper's claims against its public codebase and identify mismatches, omissions, and reproducibility risks.
args: <item>
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

Audit the paper and codebase for: $@

Derive a short name from the audit target (lowercase, hyphens, no filler words, ≤5 words). Use this short name for all files in this run.

## Required Artifacts

Every run must leave these on disk:
- `outputs/.plans/<name>.md`
- `outputs/<name>-audit.md`
- `outputs/<name>-audit.provenance.md`

Once evidence gathering starts, never end with chat-only output. If the repo or paper is unreachable, write a partial audit plus provenance with `Verification: BLOCKED`.

Requirements:
- Before starting, outline the audit plan: which paper, which repo, which claims to check. Write the plan to `outputs/.plans/<name>.md`. Briefly summarize the plan to the user and continue immediately.
- Use the `researcher` subagent for evidence gathering and the `verifier` subagent to verify sources and add inline citations when the audit is non-trivial.
- Compare claimed methods, defaults, metrics, and data handling against the actual code.
- Call out missing code, mismatches, ambiguous defaults, and reproduction risks.
- Read the paper and the actual code before characterizing either; mark each claim verified, inferred, or blocked honestly; never invent results.
- Save exactly one audit artifact to `outputs/<name>-audit.md`.
- End with a `Sources` section containing paper and repository URLs, and write `outputs/<name>-audit.provenance.md` (date, paper + repo identifiers, claims checked, verification status). Verify both files exist on disk before responding.
