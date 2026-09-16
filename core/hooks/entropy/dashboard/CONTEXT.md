# dashboard
> The entropy report: running every check over one repo, and what the findings look like.

Split from [`../`](../CONTEXT.md) 2026-08-18, when an eighth check pushed that directory past the
crowding signal. The boundary was already the parent's own one-line description — *the dashboard **and**
the checks it runs* — so the split cost no new idea, only the hop.

A check lives next door, not here: one that moved in would become invisible to the commit gate,
which imports the checks directly. Which of the two callers blocks and which reports is
[`../`](../CONTEXT.md)'s own head.

One repo per run (ruled 2026-09-04, Lucas): no argument means this repo, `--repo <path>` names
another. Which projects exist is [`PROJECTS.md`](../../../../PROJECTS.md).

`core/tools/wos/roundup` runs it at every session close, into the `entropy:` block of that repo's
`ISSUES.md`. The ratchet that keeps the counts falling is
[`test_corpus_ratchet.py`](../../../tools/test/workspace/ratchets/test_corpus_ratchet.py).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`entropy-dashboard.py`](entropy-dashboard.py) | [`entropy-dashboard.pyi`](entropy-dashboard.pyi) | `collect`, `main` | The entropy dashboard. Runs every Level 0 check over ONE repo — this one, or the `--repo` named — and writes one generated report, so agents and Lucas read a pre-computed file instead of re-scanning the tree. Zero-token, no LLM. |
| [`entropy_report.py`](entropy_report.py) | [`entropy_report.pyi`](entropy_report.pyi) | `local_seed`, `render` | The entropy report: what the dashboard's findings look like on the page. |
| [`entropy_trend.py`](entropy_trend.py) | [`entropy_trend.pyi`](entropy_trend.pyi) | `baseline`, `format_trend` | The dashboard's own history, re-derived from git rather than stored. |
<!-- routing:end -->
