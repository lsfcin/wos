# [Project Name]
> Project scaffolding templates — CONTEXT.md, README.md, SPECS.md, ROADMAP.md skeletons
> goal: none
> spec: none
<!-- goal: [name](../../brain/goals/<name>.md) — required on line 3 by pre-commit 1c, or 'none'.
     spec: flip to 'SPECS.md' once this module has a contract (author from _templates/SPECS-module.md);
     'none' opts out. New modules under code/ MUST declare a spec — see code/ROADMAP-spec-drive.md. -->

<!-- What: workspace routing and agent entry point for this project.
     Not here: feature list (→README.md), architecture decisions (→SPECS.md), setup steps (→SETUP.md).
     Keep it minimal — agents load this first; every extra line costs tokens on every task. -->

## Overview
<!-- Optional. 2–3 sentences: what this project is, its current state, key constraints.
     Skip if README.md already covers it well and this project has no agent-specific context to add. -->

<!-- ↑ Auto-managed by context_synchronizer.py. Do NOT edit the routing block manually.
     Add subdirectories via the filesystem; the sync script updates this table. -->

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`ISSUES.md`](ISSUES.md) | [Project Name] — Issues |
| [`README.md`](README.md) | [One-line tagline — what it is and why it matters.] |
| [`ROADMAP.md`](ROADMAP.md) | [Project Name] — Roadmap |
| [`SETUP.md`](SETUP.md) | Everything needed to run this project locally from scratch. |
| [`SPECS-module.md`](SPECS-module.md) | SPEC: [module name] |
| [`SPECS.md`](SPECS.md) | Design decisions, algorithms, conventions, and architecture rationale. |
<!-- routing:end -->
