# [Project Name] — Issues

<!-- What is currently UNTRUE about this project that we know about. Three kinds live here and
     they are kept apart on purpose:

       1. Confirmed bugs, hand-written, numbered sequentially (B1, B2, …). Numbers are permanent
          and never reused. Keep root-cause analysis here; DELETE a resolved entry, because git
          is the history and the regression spec test/**/b<N>-* is the durable proof.
       2. The repo's entropy findings, inside the generated entropy block.
       3. The repo's verification result, inside the generated verify block.

     RULE (enforced by the issues-gate hook): a bug flips to FIXED only when a matching
     regression spec exists at test/**/b<N>-*.* and passes. Open bugs may carry an xfail spec
     that encodes the expected failure. See workspace ROADMAP-verify.md.

     RULE (generated blocks): never hand-edit inside a block, and never write a measured number
     outside one. A copied count is exactly the drift these checks exist to catch. The FIXED gate
     governs the hand-written half only. Same contract as the routing block in CONTEXT.md --
     see core/SCHEMA.md § The .md type system. -->

## B1 — [Short symptom title]

**Symptom:** What is observed, when, and how consistently.

**Repro:** Exact steps or fixture scene that reproduces it. If confirmed visually, export
the scene/state as a test fixture before moving on.

**Root cause:** Fill when found — mechanism, not just location.

**Workaround:** If any.
