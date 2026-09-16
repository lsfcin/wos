---
description: Plan or execute a replication workflow for a paper, claim, or benchmark.
args: <paper>
type: research-brief
confirm: plan
agents: researcher
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- Search: use `web_search`
- Fetch URLs: use `fetch_content`
- Agent delegation: use `subagent` when available
- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Design a replication plan for: $@

Derive a short name from the target (lowercase, hyphens, no filler words, ≤5 words). Use it for all files in this run.

## Required Artifacts

Every run must leave these on disk:
- `outputs/.plans/<name>-replication.md` — always (the plan)
- on execution: results/scripts in a reproducible layout + `outputs/<name>-replication.provenance.md`
- `CHANGELOG.md` entries for multi-step or resumable runs

`confirm: plan` — this flow blocks for the execution-environment choice (Step 4) before running anything. Once execution
starts, never end with chat-only output. Do not call the outcome replicated unless the planned checks passed; mark
unverified steps `blocked`.

## Workflow

1. **Extract** — Use the `researcher` subagent to pull implementation details from the target paper and any linked code.
   If `CHANGELOG.md` exists, read the most recent relevant entries before planning or resuming.
2. **Recipe pass** — For ML training, fine-tuning, benchmark, or dataset-heavy targets, perform a recipe extraction
   before execution planning. Link each claimed result to the exact dataset, method, hyperparameters, compute
   assumptions, metric, and code path that produced it. Validate dataset availability/schema when possible and mark
   unchecked details as `unverified` instead of assuming they are usable.
3. **Plan** — Determine what code, datasets, metrics, and environment are needed. Be explicit about what is verified,
   what is inferred, what is still missing, and which checks or test oracles will be used to decide whether the
   replication succeeded.
4. **Environment** — Before running anything, ask the user where to execute:
   - **Local** — run in the current working directory
   - **Virtual environment** — create an isolated venv/conda env first
   - **Docker** — run experiment code inside an isolated Docker container
   - **Plan only** — produce the replication plan without executing
5. **Execute** — If the user chose an execution environment, implement and run the replication steps there. Save notes,
   scripts, raw outputs, and results to disk in a reproducible layout. Do not call the outcome replicated unless the
   planned checks actually passed.
6. **Log** — For multi-step or resumable replication work, append concise entries to `CHANGELOG.md` after meaningful
   progress, failed attempts, major verification outcomes, and before stopping.
7. **Report** — End with a `Sources` section containing paper, dataset, documentation, and repository URLs.

Do not install packages, run training, or execute experiments without confirming the execution environment first.
