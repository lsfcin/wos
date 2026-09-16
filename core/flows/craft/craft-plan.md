---
description: Loops 0-2 of the craft flow — clarify the ask, plan it adversarially, ground it in the code that exists.
args: <carry file>
---
## Loop 0 — Clarify

**Level:** high (max if ambitious/innovative). **Input:** the raw request + user interview. **Output:** `0-clarify.md`.
The only interactive loop.

**Spec precedes code (SDD).** If any target module under `code/` is spec-locked — its `CONTEXT.md` carries `> spec:
<path>` and that `SPEC.md` is `status: locked` — **read the SPEC.md first** (the `spec-read-gate` will block edits
otherwise) and treat its `## Invariants` as pre-set acceptance criteria: fold them into `criteria:` below so the flow
verifies them. The module spec is the contract; this run must not violate it. See `code/ROADMAP-spec-drive.md`.

Interview the user (don't assume — workspace rule) until you can fill every field. Then apply the **bakery gate**:
verdict `padaria` iff ALL hold — ≤2 files touched, no new public API, no schema/data migration, an existing pattern in
the repo covers it, revert fully undoes it, criticality=low|normal. Otherwise `standard` (or `critico` if
criticality=critical).

```markdown
## Carry
<fill per template above; branch/test-cmd may be TBD until Loop 1/2>

## Clarify
intent: <what, one sentence>
motivation: <why now>
refs: <links, files, prior art>
scope-files: <known files/folders touched>
expected-result: <observable end state>
ambition: <minimal|solid|showcase>
criticality: <low|normal|critical> tolerance: <what failure is acceptable>
criteria: C1..Cn <objective, testable>
innovation: <none|some|core — is creativity the point?>
verdict: <padaria|standard|critico>
keep-trail: <yes|no>

## Permission Panel (supervision profile — copy into Carry `supervision:`)
io-signoff: <yes|no>                       # human OKs each module/step I/O boundary before code — default NO (agent proceeds)
arch-review: <none|per-feature|periodic>   # recurrent concept-symmetry review cadence — default NONE
arch-review-supervised: <yes|no>           # human checks the arch review — default NO
```

**Permission-panel interview (feature folder).** After the criteria are settled, ask the user three short questions and
record the answers above; the **recommended defaults are permissive** so the agent runs unattended and cheap. The
contract itself is never optional — only *human sign-off on it* is. Ask: (1) "Do you want to acknowledge each
module/step I/O boundary before I implement? (default no)"; (2) "Should I run the concept-symmetry architecture review —
never, once per feature, or as a periodic sweep? (default never)"; (3) if arch-review ≠ none, "Do you want to check that
review yourself, or let me? (default me)".

**Padaria shortcut:** verdict `padaria` → skip Loops 1, 3, 3.5, 4a, 5. One medium-level session does: append a ≤5-line
micro-plan to `0-clarify.md`, execute Loop 2 (branch), edit, run the **existing** test suite, execute Loop 6. Two files
total (`0-clarify.md`, `6-ship.md`). The flow must never cost more than the task.

**Flags:** none (nothing before it). If the user can't state criteria, the task isn't ready — stop, don't start the
flow.

## Loop 1 — Plan

**Level:** high. **Input:** `0-clarify.md`. **Output:** `1-plan.md`.

Plan, then **adversarially review your own plan assuming smaller models will execute it**: every task row must be
executable by its assigned level from the row text + Carry block alone — no implied context, no "as discussed".
Ambiguity
that a medium-level model would trip on is a FATAL. Fix or escalate row levels, then re-review — **exit when a pass
leaves
zero unresolved FATALs; iteration cap: at most 3 passes.** At the cap, stop and carry the surviving FATALs into `## Plan
Review` as `verdict: FAIL` with each one named — an adversary can always find something, so the bound is what keeps this
a review instead of a hang (`core/flows/CONTEXT.md` § Rules that hold for every flow). Copy the final task rows into the
Carry `tasks:` digest (later loops read only one file — this is how they see the plan). Add a line referencing this plan
to the project's `ROADMAP.md` (workspace policy).

```markdown
## Carry
<copied + branch name and test-cmd now filled>

## Plan
branch: <name>
| id | task | files | done-when | level | effort |
|----|------|-------|-----------|------|--------|
| T1 | ...  | ...   | <objective check> | medium | medium |

## Plan Review (adversarial, assume small executors)
- <risk found> → <fix applied | level raised on Tn>
verdict: PASS | FAIL
```

**Flags:** review exposes a gap in intent that planning can't fix → `RETURN loop=0 reason=intent-gap`. Plan exceeds ~10
rows → `RETURN loop=0 reason=split-needed` (feature too big for one flow run).

## Loop 2 — Ground

**Level:** low. **Input:** `1-plan.md`. **Output:** `2-ground.md`.

Mechanical grounding: create the branch from the correct base; verify every path in the plan's `files` column exists (or
its parent dir does, for new files); verify `test-cmd` actually runs (may be red, must not error out).

**Git Flow (enforced).** The branch MUST be `feature/<name>` off `develop` (or `hotfix/<name>` off `main`) —
`core/hooks/git/gitflow_gate.py` blocks commits on `main`/`master`/`develop` or any non-flow branch name in `code/`
repos, so a wrong branch here fails at Loop 6 ship. If the project has no `develop` yet, create it from `main` first.

```markdown
## Carry
<copied>

## Ground
branch-created: <name> base: <ref>
paths: <n>/<n> ok | missing: <list or none>
test-cmd-runs: yes|no <output tail if no>
```

**Flags:** >20% of paths missing/renamed, or test-cmd errors → `RETURN loop=1 reason=stale-plan evidence=<list>`.
