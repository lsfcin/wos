# Agents
> Agent definitions; load as system prompt to spawn a specialist worker.

Each file is a complete operating context for one agent role. In Claude Code, spawn a worker by
passing the file content as the system prompt via the Agent tool.

**One pipeline, in order: `writer` drafts from evidence `researcher` gathered, `verifier` adds the
citations afterward, `reviewer` grades the result.** Who each one is, is the routing table's job —
it reads their frontmatter, which is the same text their spawner gets.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`_template.md`](_template.md) | One line — what evidence or output this worker produces. |
| [`lead.md`](lead.md) | Orchestrates research workflows; plans tasks, delegates to worker agents, synthesizes results. |
| [`researcher.md`](researcher.md) | Gather primary evidence across papers, web sources, repos, docs, and local artifacts. |
| [`reviewer.md`](reviewer.md) | Simulate a tough but constructive AI research peer reviewer with inline annotations. |
| [`verifier.md`](verifier.md) | Post-process a draft to add inline citations and verify every source URL. |
| [`writer.md`](writer.md) | Turn research notes into clear, structured briefs and drafts. |
<!-- routing:end -->
