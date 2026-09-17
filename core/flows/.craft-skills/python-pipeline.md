---
name: python-pipeline
description: Design patterns earned by /craft runs on Python pipelines — what the next plan should
  do differently, not what one repo happens to contain.
domain: python-pipeline
tags: [facade, integration-gap, validation-order, cli]
provenance: code/isoroll-content commit ce81655 — the export-manifest chain, distilled in
  core/flows/craft/prior-art.md before its trail was deleted
---

# python-pipeline

Reusable design patterns earned by `/craft` runs in this domain. Loop 1 greps this directory before
authoring a plan; Loop 6.5 appends to it. A pattern belongs here only if it would change how the
NEXT plan is written — a fact about one repo does not.

## A loader reused for validation opens the world before the validator can reject it

**Where it came from.** `build_manifest` imported `scene_assemble.load_kit`, which PIL-opens every
kit piece PNG *before* `wall_schema.validate_manifest` could emit its designed `[FAIL] + exit 1`. A
missing asset therefore crashed with an uncaught `FileNotFoundError` instead of reaching the
graceful validation path. The unit suite could not see it: the tests fed `validate_manifest` a
hand-mutated dict and never drove `build_manifest` against a directory with a genuinely missing
file. Loop 5 caught it, Loop 3 split `load_kit_meta` out of `load_kit`, and the chain shipped.

**The pattern.** When a function is reused for its *metadata* by a caller that means to validate,
the reuse silently imports the original's side effects — and reading metadata is a different job
from loading content. Split the cheap read out and let the validator run first.

**What to do at plan time.** For any path that validates before acting, name in Loop 3 which call
touches the filesystem first, and make at least one Loop 4a test drive the *real* entry point
against a genuinely missing input rather than a mutated in-memory structure. A test that constructs
the bad state by hand cannot find an ordering bug, because ordering is what it skipped.
