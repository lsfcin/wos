---
name: dedup
description: Semantic duplication audit for a code project, defaulting to the one in the working directory: near-duplicate logic that the verbatim-clone gate misses.
---

# Dedup skill

Arguments: $ARGUMENTS

---

## Why this exists

The pre-commit jscpd gate blocks verbatim/near-verbatim clones. Agents rarely paste —
they REGENERATE similar logic with new names. Token-based tools miss that. This audit
finds semantic duplicates on a cadence (run at roundup or weekly).

## Protocol

1. Resolve project root (argument, else nearest `.codegraph/` ancestor of cwd).
2. Candidate harvest — collect suspicious pairs via:
   - `codegraph query`/`codegraph explore` for same-signature functions across files
     (same arity + similar parameter names, or same return shape).
   - Name families: `grep -o` exported function names from interfaces (`.d.ts`/`.pyi`),
     cluster by shared stems (e.g. `applyTileFog` / `applySliceFog` / `applyTokenFog`).
   - jscpd at low threshold for leads (report only): `npx jscpd <src> --min-tokens 35
     --min-lines 5 --reporters consoleFull --silent`.
3. For each candidate pair: read both implementations; classify —
   - **DUPLICATE** — same behavior, different spelling → extract shared function, migrate
     both callers, delete copies (Strangler Fig: never two live implementations).
   - **SIBLING** — legitimately parallel (different axis of variation) → leave; note if a
     shared core could be factored later.
   - **DIVERGED COPY** — started equal, drifted → the dangerous one; decide the canonical
     behavior FIRST, then unify. Check git log of both files for the fork point.
4. Fix DUPLICATEs directly (respect facade + 200-line gates). For risky unifications,
   file a ROADMAP item instead of a blind refactor.
5. Report: pairs found / fixed / deferred, with file:line references.
