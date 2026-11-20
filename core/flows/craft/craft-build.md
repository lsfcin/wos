---
description: Loops 3-4b of the craft flow — architecture, contract layout, tests first, then code until green.
args: <carry file>
---
## Loop 3 — Architecture

**Level:** high (max if critico). **Input:** `2-ground.md`. **Output:** `3-arch.md`.

Design the high-level shape: folders, files, classes, responsibilities, key function signatures. Then a same-session adversarial evaluation pass: does every criterion C1..Cn have a home and a **testable boundary**? Would a medium-level model implementing file-by-file make a wrong guess anywhere? Fix before writing the verdict.

**Concept-Symmetry Review (recurrent · runs per Carry `supervision: arch-review`).** When `arch-review=per-feature`, run it here; when `periodic`, skip inline and run it as a standalone sweep on cadence; when `none`, skip. It guards conceptual integrity — the semantic soundness of the *whole* project, not just this feature. Two layers:
- **Checklist (judgment):** do alike things look alike (parallel structures named/shaped alike)? Is naming coherent across modules (one concept = one name, no synonyms)? Are module boundaries consistent (same kind of thing split the same way)? Does this design keep the project's mental model sound, or bolt on an asymmetry?
- **Automation:** run `codegraph` (via bash) over the touched project for structural outliers/asymmetry, and the `/dedup` skill for regenerated near-duplicate logic the jscpd gate misses. Feed both into the checklist.
If `arch-review-supervised=yes`, present the findings and wait for the user's call before the verdict; else the reviewer (fresh session, not the author) rules.

```markdown
## Carry
<copied>

## Architecture
<per file: path — responsibility — key functions/signatures — plan task ids>

## Evaluation
criteria-coverage: C1→<where> ... Cn→<where>
boundaries: <how each criterion will be tested>
verdict: PASS | FAIL <reason>

## Concept-Symmetry Review (omit if arch-review=none)
checklist: alike-look-alike=<ok|issue> · naming-coherent=<ok|issue> · boundaries-consistent=<ok|issue> · model-sound=<ok|issue>
codegraph: <structural outliers/asymmetries, or none>
dedup: <near-duplicate logic found, or none>
supervised: <n/a | findings shown → user verdict: OK|CHANGES> 
verdict: PASS | FAIL <reason>
```

**Flags:** an acceptance criterion cannot be satisfied by any reasonable design → `RETURN loop=1 reason=criterion-infeasible`; two criteria contradict → `RETURN loop=0 reason=criteria-conflict`.

## Loop 3.5 — Contract Layout (feature folder · mandatory · contract-first)

**Level:** high. **Input:** `3-arch.md`. **Output:** `3b-contracts.md`.

This is the heart of the feature folder: **lay out every module/step I/O contract before any implementation**, so the connection graph is defined in advance and the code merely fills the placeholders. The contract is mandatory regardless of the supervision panel; only the *human sign-off* on it is optional.

1. For every `code/` module the architecture touches, create/update its `SPEC.md` from `code/_templates/module.SPEC.md` — fill `Inputs`, `Outputs`, `Invariants` from the architecture's signatures + the Carry criteria; set `> spec:
   SPEC.md` in the module `CONTEXT.md`. (This is also what satisfies the standing spec gates — see
   `code/ROADMAP-spec-drive.md`.)
2. Generate the interface skeleton (the `.pyi`/`.d.ts`/`.dart.api` stubs the post-edit hook already emits) so the boundaries exist as types before bodies.
3. Wire the **connection graph**: for each planned edge `A → B`, assert `A.outputs` type matches `B.inputs` type. Run `core/tools/wos/spec/contract-check <project>` — it fails if any planned module lacks a contract or any edge's types mismatch.
4. **Human gate:** if Carry `supervision: io-signoff=yes`, present the I/O map (modules, their in/out, the edges) and wait for an explicit OK before Loop 4a; otherwise proceed.

```markdown
## Carry
<copied>

## Contracts
modules: <module — SPEC.md path — status: draft|locked>
edges: <A.output:type → B.input:type — MATCH|MISMATCH>
contract-check: <core/tools/wos/spec/contract-check output last line>
io-signoff: <n/a | requested → APPROVED by user | pending>
```

**Flags:** an edge cannot be made to type-match without a design change → `RETURN loop=3 reason=contract-gap`; a criterion has no home in any module contract → `RETURN loop=1 reason=criterion-uncontracted`.

## Loop 4a — Tests First

**Level:** medium. **Input:** `3b-contracts.md`. **Output:** `4a-tests.md`.

TDD: write functional/unit tests **before** implementation code, one or more per criterion, placed at the boundaries named in the architecture. Run them; confirm they fail for the right reason (missing behavior, not syntax/import errors).

```markdown
## Carry
<copied>

## Tests
| test file | covers | asserts |
|-----------|--------|---------|
red-run: <n> failed as expected | wrong-failures: <none or list>
```

**Flags:** a criterion is untestable at the designed boundaries → `RETURN loop=3 reason=no-boundary`; untestable as *written*
regardless of design → `RETURN loop=1 reason=criterion-untestable`.

## Loop 4b — Code Until Green

**Level:** medium (per plan-row levels). **Input:** `4a-tests.md`. **Output:** `4b-code.md`.

Implement plan tasks until `test-cmd` is fully green. Append one `attempt` line per red run — this log is the escalation evidence. **Never edit a test to make it pass**; a wrong test is a flag, not a patch.

```markdown
## Carry
<copied>

## Code
attempt 1: <tasks done> → <n red> <failing test names>
attempt 2: ...
ESCALATED ... (if any)
green: yes run: <test-cmd output last line>
touched: <files>
```

**Flags:** 3 red attempts at default level + 3 more at escalated level → decide by evidence: failing test contradicts a Carry criterion → `RETURN loop=4a reason=test-wrong`; test is right but the design fights it → `RETURN loop=3 reason=design-fights-tests`.
