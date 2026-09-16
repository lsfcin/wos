---
description: Set up a recurring or deferred research watch on a topic, company, paper area, or product surface.
args: <topic>
type: utility
confirm: none
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Scheduling: use available scheduling tools to create recurring or deferred follow-ups
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Create a research watch for: $@

Derive a short name from the watch topic (lowercase, hyphens, no filler words, ≤5 words). Use this short name for all
files in
this run.

Requirements:
- Before starting, outline the watch plan: what to monitor, what signals matter, what counts as a meaningful change, and
  the check frequency. Write the plan to `outputs/.plans/<name>.md`. Briefly summarize the plan to the user and continue
  immediately.
- Start with a baseline sweep of the topic.
- Use available scheduling tools to create the recurring or delayed follow-up instead of merely promising to check
  later.
- Save exactly one baseline artifact to `outputs/<name>-baseline.md`.
- End with a `Sources` section containing direct URLs for every source used.
- Never invent sources or findings: every claim in the baseline must trace to a fetched source. If scheduling or a fetch
  fails, report the failure honestly and record the capability as blocked — do not pretend the watch is armed.
