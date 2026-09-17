# SPEC: [module name]
<!-- Machine-parseable module contract (spec-driven development). Keep the header keys below. -->
spec-version: 0
status: draft
verify: none

<!--
  status:  draft  = spec exists; the read-gate is NOT armed yet, conformance not wired.
           locked = read-gate armed — editing this module's files requires reading this SPEC first.
  verify:  how the ## Examples are mechanically checked. One of:
             none                      → examples checked by eye only (draft-conformance)
             make verify-fast          → examples run inside the project's verify:fast (Makefile)
             npm run verify:fast       → same, npm projects
           A locked spec with a runnable `verify:` is fully spec-driven: a broken example
           turns verify:fast red and the existing commit gate blocks it.
-->

## Inputs
<!-- What this module consumes. Types/shapes/preconditions. One item per line, testable phrasing. -->

## Outputs
<!-- What it produces. Types/shapes/postconditions. One item per line. -->

## Invariants
<!-- Properties that must ALWAYS hold, independent of inputs. One per line, checkable phrasing.
     These are the contract the code may never violate — the source of truth for reviewers and gates. -->

## Examples
<!-- Concrete input → expected output pairs. These ARE the executable conformance cases when
     `verify:` names a runner. Prefer examples that map 1:1 to a test in the project's suite. -->

## Notes
<!-- Rationale, a wiki-link to this project's own goal, .craft provenance, sibling SPEC.md. -->
