# routing — Specs
> What the routing generator writes into an authored document, and where every file's one-line
> description has to come from.

Companion to [`CONTEXT.md`](CONTEXT.md), which routes into this directory. Moved out of
[`../SPECS.md`](../SPECS.md) on 2026-09-05: the enforcement layer's spec had grown to 376 lines
against a 200 cap, and a rule about what a generator writes belongs beside the generator rather than
in the root's law.

## The `CONTEXT.md` routing block

`context_synchronizer.py` runs on every edit (via `post-edit.sh`, which also re-syncs the parent
directory) and every commit, keeping each directory's `## Routing` block true unmaintained: it
**adds** a new file, taking its description from the first source that answers — the first-line
comment (code, below any shebang), a module docstring's first line (`.py`), `description:`
frontmatter then the line-2 `> ` blurb (`.md`), or the ` — ` usage comment (extensionless scripts);
**removes** entries for deleted files; **links** interfaces to their source; **folds** a leaf
directory under `FOLD_FILES` into the parent block and **links** one at or above it; **warns** when a
directory exceeds `WARN_FILES` direct files. Those are two numbers because they are two questions —
*substantial enough to route to* is not *too crowded to read* (2026-09-06, [`limits.env`](../limits.env)).

**Never edit inside the `<!-- routing:start/end -->` sentinels** — the next sync overwrites it.
**Renames are not tracked**: the old entry disappears and the new file arrives with a placeholder.
**`<!-- x:start -->` does not mean generated.** `routing` `projects` `entropy` `verify` `norms`
`stats` `done` `goals` have writers; `steps` and `data` are delimited so a *test* can parse them
and a **human** writes them. A sweep that skips every marker skips real writing (2026-09-14).

**Every description is bounded at `DESC_LIMIT`; only a `.md`'s is also rebased.** A `.md` blurb and a
subdirectory blurb were written to sit under their own heading, so [`hoist.py`](hoist.py) rewrites
their relative links for the parent directory. A code file's comment has nothing to rebase, and was
exempt from the bound too until 2026-09-11 on the grounds that it is authored as this table's
one-liner — but `comment_paragraph` reads the whole opening paragraph, so it is no more a line than
the blurb is. Ten rows were over; the fix is a paragraph break in the source, never a cut in the
table, which `entropy_context.check_truncation` asserts at zero.

## First-line descriptions

Every scanned file begins with a one-line description, because `context_synchronizer.py` reads it as
the canonical description. Enforced at **Write** (`checks/first-line-gate.py` blocks), at **Edit** (a
reminder prints, the edit stands), and at **commit** — `entropy_context.check_description`, run by
`checks/type-gate.py` over the files the commit adds.

**The commit gate is the load-bearing one.** `first-line-gate.py` only fires under
`if not os.path.exists(file_path)`, so a file written by a generator, a heredoc, `git checkout` or an
agent not running our hooks is never asked. **An edit-time check only covers the harness path; the
staged set is what covers everyone.**

**The check asks the generator, never its own pattern table** — `workspace_meta.file_description()`,
the same call whose empty return makes the generator write the placeholder. **A marker is not
evidence of a discipline problem until the generator has been asked whether it can answer it**:
check the extension's entry in [`workspace_meta.py`](workspace_meta.py) before writing any
description by hand, because a hand sweep gets re-filled.

**A file that cannot carry a comment is described in [`../described.txt`](../described.txt)
instead** — the answer for a file whose *content is data a parser reads*. Found 2026-08-20 on seven
DSL fixtures, where **adding the comment is not merely useless but destructive**: the parse test
passed with a `#` first line while the round-trip test went red, because the parser silently drops
it. That parse-only green is the silent pass [`core/SPECS.md`](../../SPECS.md) § Conventions warns
about.
