# Flows
> Workflow protocols; each names the agents and steps to execute.

Contract for the frontmatter, the `type` disciplines, and the `uses:` composition DAG:
[`core/SCHEMA.md`](../SCHEMA.md). Canonical wording to copy when writing a flow:
[`_template.md`](_template.md).

## Rules that hold for every flow

These were extracted from the craft monolith (2026-07-23) because they were never specific to one
flow:

- **The artifact is the memory.** A flow's durable output is a file on disk, not the chat. A run
  that ends chat-only after work started produced nothing. State that survives the session is what
  lets the next session — or a cheaper model — pick the work up.
- **Delegate gathering, never synthesis.** Subagents collect; the flow that owns the artifact writes
  it. A synthesis handed to a subagent comes back as a lossy retelling.
- **A fresh session reads exactly one file.** When a flow relays work between sessions, each one
  receives its own step plus a single input file — never conversation history. This is how a flow
  *saves* tokens instead of spending them.
- **Size is a signal.** A step whose artifact keeps growing past its cap is a step that is too big.
  Split the work; do not raise the cap.
- **Loops are bounded.** Returning to an earlier step is legal iteration only with an exit condition
  and a numeric cap, and only if state changed. See `_template.md` § Execution Loops.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`craft/`](craft/CONTEXT.md) | The engineering cluster owned by the `craft` skill — build work in file-relayed loops. Invoked as `/craft`. |
| [`research/`](research/CONTEXT.md) | Research-workflow protocols owned by the `research` skill. Invoked as `research <verb>` — filename = command tail. |

| File | Description |
|------|-------------|
| [`_template.md`](_template.md) | One line — what durable artifact this flow produces. |
| [`mechanism-search.md`](mechanism-search.md) | Systematic search for social mechanisms (individual motive → collective effect) against a quantified ralo — forced-diversity generation, deliberative human filter, output ready for a test-to-kill pilot. |
<!-- routing:end -->
