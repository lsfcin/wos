# Code — Specs
> Engineering conventions, architecture decisions, and process rules for all code/ projects.

## Hook Enforcement Reference

Which hook fires when, and what it blocks: [`core/hooks/SPECS.md`](../core/hooks/SPECS.md). That
file is the enforcement layer's own contract and holds the table once; repeating a row here would
be a second copy to keep true.

Two rules are `code/`-specific and live only there: a staged `.ts`/`.tsx` under `code/` with ESLint
R1-R6 violations **hard-blocks** the commit, and `post-edit.sh` Prettier-formats in place while
printing R1-R6 violations as non-blocking warnings.

What the hooks catch is the floor, not the standard — everything below is yours to enforce.

## Engineering Constraints

These are enforced by code review, not hooks. Violation = redo before continuing.

- **One responsibility per file** — if you need to describe a file with "and", split it
- **Never copy-paste** — if the same logic appears twice, extract a function or class first
- **Names must be guessable** — file, class, function, variable names without opening the file
- **Flat over deep** — prefer sub-modules over nested directories beyond 2 levels
- **After each prompt** — is the code cleaner or messier than before? If messier, redo
- **Run test suites under a memory cap** — `(ulimit -v 3000000; timeout 120 <runner>)`. A runaway
  loop in the code under test, or a failing assertion whose diff is enormous, is allocated by the
  test process and can take the editor down with it: pytest's assertion introspection turned one
  unbounded list into an OOM that killed VS Code three times before it was diagnosed (aiwbot,
  2026-07-29). Capped, the child dies instead. Add `--assert=plain` when a failure is expected to
  involve a huge object
- **Eyeball output whose shape is the deliverable** — chat bubbles, rendered docs, images. Two
  bugs in aiwbot (an answer reposted whole; `(1) (1/10)` double counters) passed every assertion
  in their own spec file and were caught by printing the result and reading it
- **Two sides of a comparison that share a derivation cannot check that derivation** — and the
  test will be green while they are both wrong. isoroll's parity oracle scaled the expected and
  the actual by the same wrong constant (CP-1), then agreed on a floor that was nine tenths
  undrawn (CP-3): both sides read the same massing. Make the two sides come from different places
  — one measured off the live system, one from the spec — or the green means only "consistent"
- **Mutation-test an oracle before trusting it** — break the thing it is supposed to catch, on
  purpose, and confirm it goes red. isoroll's first CP-4 wall check passed against the very bug it
  was written for; a two-minute revert-and-run is what said so

<!-- routing:start -->
## Routing

| Part | Description | Governs | Enforced by |
|------|-------------|---------|-------------|
| [`SPECS-git.md`](SPECS-git.md) | Which branches exist, what may be committed where, and when work is pushed. | every repo under code/, and the workspace repo itself | core/hooks/git/gitflow_gate.py, core/hooks/post-commit |
| [`SPECS-structure.md`](SPECS-structure.md) | How a project is laid out: its files, its module specs, and its facade. | code/<project>/ | core/hooks/facade/, core/tools/wos/spec-scan |
| [`SPECS-style.md`](SPECS-style.md) | How a file is written, how big it may get, and when a directory splits. | every file under code/ | core/hooks/checks/, eslint.shared.js |
<!-- routing:end -->
