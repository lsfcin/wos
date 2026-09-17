# Style and size
> How a file is written, how big it may get, and when a directory splits.
> governs: every file under code/
> enforced-by: core/hooks/checks/, eslint.shared.js

## Style Rules (R1-R6)

Enforced for TypeScript projects via ESLint (`code/eslint.shared.js` + project `eslint.config.js`).
Python/other languages: induced via this doc.

| Rule | Description | ESLint enforcement |
|------|-------------|-------------------|
| **R1** | One statement per line — no semicolon-separated statements | `max-statements-per-line` + `curly` |
| **R2** | One function/method call per statement — no nested calls `foo(bar())`, no method chaining `arr.filter().map()`. Use intermediate variables | `local/one-call-per-statement` |
| **R3** | Single return per function — use if/else to collect result in variable | `local/single-return` |
| **R4** | No untyped casts — no `as any` in TS, no `# type: ignore` in Python without explanation | `@typescript-eslint/no-explicit-any` |
| **R5** | Max 40 lines per function/method (blank lines and comments excluded) | `max-lines-per-function` |
| **R6** | Max 2 property accesses from root — `a.b.c` is the limit; `a.b.c.d` must be split: `const x = a.b.c; x.d` | `local/max-chain-depth` |

**Canonical shared config:** `code/eslint.shared.js` — exports `localPlugin` (3 custom rules) and
`sharedRules`. Each TS project imports both.

**Enforcement hooks:**
- `post-edit.sh` — runs Prettier (auto-format) and surfaces ESLint violations after every edit (non-blocking)
- `pre-commit` — hard-blocks commit if any staged TS file under `code/` has ESLint errors

**Why these rules?** Dense compressed lines force agent to rebuild context before proposing fixes.
Each nested call or chained method adds AST depth that must be unwound. Single-return and
intermediate variables keep every expression flat and independently debuggable. The effect is
shorter debugging sessions and fewer context-limit hits.

## First-Line Description

Every code file must start with a one-line description comment. New files without it are blocked by `pre-edit.py`.

| Language | Format |
|----------|--------|
| Python / YAML / TOML | `# Short description` |
| JS / TS / Dart | `// Short description` |
| CSS / SCSS | `/* Short description */` |
| HTML | `<!-- Short description -->` |
| LaTeX | `% Short description` |
| Markdown | `# Title` (heading is the description) |

One sentence, no period, ≤80 chars. Describe *what*, not *how*.

## File Size Policy

Applies to `.js .ts .tsx .py .dart .html .css .scss`:

`WARN_LINES` warns at commit, `BLOCK_LINES` rejects the commit and the edit, and both numbers live
in `core/hooks/limits.env` — the copy that used to sit here as a table named the warn and the block
one ruling behind, for six days. Ask the law: `core/run hooks/checks/line_counts.py`.

Near limits: extract modules, separate orchestration from implementation logic.

## Splitting an over-full directory

`WARN_FILES` / `BLOCK_FILES` (`core/hooks/limits.env`). A large routing table is the
directory saying it holds more than one responsibility — but the split costs a routing hop, so it
has to earn it. Five things learned draining `core/hooks`, `core/tools`, `aiwbot` and `flows`,
each of which cost a session to find:

1. **Check whether it is a split or a delete, first.** The worst directory in `flows` was neither
   tangled nor needed: 14 dead modules whose own headers still named a framework the repo had
   left. **A file nothing imports is the first thing to look for in an over-full directory.**
2. **But "nothing imports it" is not proof it is dead.** Five orphan components there read as
   debris on imports plus `git log`, while the repo's own `ROADMAP.md` showed one milestone had
   *deliberately unwired* them and the next planned to reuse them. **Grep the repo's ROADMAP for
   the filename before calling it dead** — that is the step the import graph cannot give you.
3. **Each new directory must declare itself with a `CONTEXT.md`, or the split bought nothing.**
   The routing generator folds any directory under `WARN_FILES` back into its parent, so files
   move and the parent's table stays exactly as long. A split that does not shrink the parent
   table is the check being gamed, not answered.
4. **A new directory turns a flat import into a module boundary**, so the facade gate starts
   firing on imports that were legal the day before. Re-export from the new `index` /
   `__init__.py`; never import past it. Related: barrel facades **defeat tree-shaking**, and a
   `parts/` directory may not import its own parent's constants — that needs a third leaf, or the
   facade gate and a module cycle fight each other.
5. **Every subdirectory of a spec-locked module must re-declare `> spec:`.** `spec-read-gate.py`
   stops at the *nearest* ancestor that declares one, so a new subdirectory written with
   `spec: none` silently unlocks the module above it.
