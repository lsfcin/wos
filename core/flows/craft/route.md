---
description: Loop router — classify a /craft task by TYPE and dispatch to the right folder flow (padaria · feature/SDD · research · architecture). Thin: it classifies and hands off, it does not do the work.
args: <task or feature request>
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.
Agent delegation: use `Agent`/`subagent`/`task` when available; otherwise the user runs the named folder flow in a
fresh session.

Route this task: $@

This is an execution request, not a request to explain the router. Classify, record the choice, hand off.

## What this is

`/craft` is a **tree**, not one pipeline. Different task *types* need different step *sequences*. This router is the
trunk: it reads the task, runs a short classification (interview + heuristics), records the chosen folder, and
dispatches to that folder's flow. It holds no work state beyond the classification — the folder owns the run.

Full map + rationale: [`tree.md`](tree.md).

## Step R0 — Classify

Ask the user only what you cannot infer. Assign exactly one folder:

| Folder | Choose when | Shape (why it's distinct) | Flow file |
|---|---|---|---|
| `padaria` | ≤2 files, existing pattern in the repo covers it, fully revertible, criticality low/normal | no ceremony — one session does plan+code+ship | `craft-plan.md` § Padaria shortcut |
| `feature` | build or change a module/feature | contract-first: I/O laid out before code, TDD, ship | [`craft.md`](craft.md) (feature folder) |
| `research` | investigate, gather, synthesize, review literature/sources | plan→scale→gather→draft→cite→review→deliver | `core/flows/research/{sota,literature,explore,compare,recipe,replicate,review,summarize,watch,audit}.md` + `core/flows/mechanism-search.md` — pick the closest |
| `architecture` | choose between designs/patterns/technologies; a decision needing a record | problem→options→trade-offs→decision→ADR | [`architect.md`](architect.md) |

**Ambiguity rule:** if a task is "decide, then build," run `architecture` first (it emits an ADR), then `feature`
consuming that decision. If it's "research, then build," run `research` then `feature`. Chain folders; never merge
their shapes into one run.

**Guardrail — do NOT add folders casually.** A new folder is justified only when a task type needs a genuinely
different *step sequence*, not merely different content. The four above are distinct shapes. Adding a fifth requires the
same bar (and a `tree.md` entry).

## Step R1 — Record + hand off

- Record the choice as `subtree: <name>` in the Carry block the folder will create, and in `STATUS.md` (`subtree:`
  header line). For `feature`, also carry the supervision profile the feature folder's Step 0 panel fills
  (`io-signoff`, `arch-review`, `arch-review-supervised`).
- Dispatch: instruct the executor (or the user) to run the named folder flow with this task. The router adds nothing to
  the folder's own protocol — it only pins which one runs.

```
subtree=<padaria|feature|research|architecture>
→ run <flow-file> with: $@   (its own Loop/Step 0 continues from here)
```

Do not narrate the folders you did not pick. One classification line, then the folder runs.
