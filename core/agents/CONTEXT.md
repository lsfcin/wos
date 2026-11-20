# Agents
> Agent definitions; load as system prompt to spawn a specialist worker.

Each file is a complete operating context for one agent role. In Claude Code, spawn a worker by passing the file content as the system prompt via the Agent tool.

Running a worker on another harness (GPT via Codex first, to save Claude quota): [SPECS.md](SPECS.md).

**One pipeline, in order: `writer` drafts from evidence `researcher` gathered, `verifier` adds the citations afterward, `reviewer` grades the result.** Who each one is, is the routing table's job —
it reads their frontmatter, which is the same text their spawner gets.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`SPECS.md`](SPECS.md) | How a worker runs on another harness, and the traps each call has. |
| [`_template.md`](_template.md) | One line — what evidence or output this worker produces. |
| [`lead.md`](lead.md) | Orchestrates research workflows; plans tasks, delegates to worker agents, synthesizes results. |
| [`montador.md`](montador.md) | Cut what a talk does not need and fix its flow — proposes, never destroys: a per-slide cut list, and skips on a copy. |
| [`researcher.md`](researcher.md) | Gather primary evidence across papers, web sources, repos, docs, and local artifacts. |
| [`reviewer.md`](reviewer.md) | Simulate a tough but constructive AI research peer reviewer with inline annotations. |
| [`verifier.md`](verifier.md) | Post-process a draft to add inline citations and verify every source URL. |
| [`writer.md`](writer.md) | Turn research notes into clear, structured briefs and drafts. |
<!-- routing:end -->
