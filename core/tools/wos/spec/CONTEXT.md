# spec
> Whether a module under `code/` has a contract, and whether that contract is complete.

Split out of [`../`](../CONTEXT.md) 2026-09-18 at the crowding signal, on a boundary that was already there: everything else in the parent asks a question about **this workspace** — what it declares, what it costs, what a close does — and these two ask about the projects it holds.

Two questions, deliberately apart. [`scan`](scan) counts coverage and is the ceiling;
[`contract-check`](contract-check) opens the specs that exist and asks whether they are filled in.
A repo can be at 100% coverage with every contract empty, which is the failure the second one catches and the first cannot see. Both are the instruments for [`code/ROADMAP-spec-drive.md`](../../../../code/ROADMAP-spec-drive.md).

The `spec-` prefix went with the directory: a tool named for the folder it already sits in reads the name twice and says it once, which is the rule [`../../CONTEXT.md`](../../CONTEXT.md) already states for a family and its provider.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`contract-check`](contract-check) | verify every spec-locked module has a complete SPEC.md contract (Inputs/Outputs/Invariants filled); optionally type-check declared edges. Exit 1 on any gap. See code/ROADMAP-spec-drive.md. |
| [`scan`](scan) | list of module SPEC.md status (locked|draft|optout|none) Spec-driven-development coverage ceiling. A module = a dir with a CONTEXT.md under code/. See code/ROADMAP-spec-drive.md. |
<!-- routing:end -->
