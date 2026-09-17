# Workspace Root
> Canonical workspace entrypoint. Read before any task.

<!-- norms:start -->
- FILESYSTEM = source of truth. No memory, no assumptions.
- **PROVIDER-AGNOSTIC STORAGE**: the workspace owns its state, never a harness; if it insists,
symlink the path into WIS.
- A LINK HANDED OUT GETS A NAME — `core/run tools/links/cfpages`, or `--short-name` where it is created.
Targets live in [`core/tools/links/links.txt`](core/tools/links/links.txt); a doc quotes the short
link, never the mapping.
- **SECRETS STAY OUT OF GIT**: passwords, tokens, CPF/CNPJ go in a gitignored
`<subtree>/segredos.env`; the text keeps the label.
- IMPROVE WOS, after finishing MICRO (particular task), take a step back and review and refine MACRO
(structure). if it ain't feasible to do it on this session, WRITE ISSUES DOWN at the end of INBOX.md
- DON'T ASSUME, interview user if in doubt about his idea or intent.
- EXPAND ACRONYMS on first use. Aliases: [`core/SCHEMA.md`](core/SCHEMA.md) § Vocabulary.
- PLAIN WORD OVER JARGON: most precise wins, simpler breaks the tie, and a word survives only if the
sentence reads worse without it. ONE IDEA, ONE WORD. A replaced word gets a row in
[`core/SCHEMA.md`](core/SCHEMA.md) § Retired tokens, which is what finishes the rename.
- EDIT > CREATE: refine / improve **wins over** creating new, except for prototyping. Avoid scattering.
- A FILE OVER THE CAP IS CUT, NOT SPLIT. A `TYPE-<name>.md` sibling is a last resort, and Lucas's
explicit OK. Reflowing is not cutting (ruled 2026-08-31): a file is held to lines AND to characters,
so reshaping the same words satisfies neither — the way out is deleting.
- SYMMETRY IS A CORE VALUE, semantic and structural. When you find an asymmetry, write it down.
- **DONE WORK IS DELETED. GIT IS THE HISTORY.** No strikethrough, no annotated dead items.
- USE OUR TOOLS: we want those to be useful and perfected.
- REDUCING IS THE WAY: improve/extend by cutting size; growing the workspace takes Lucas's OK first.
Cut where a line is READ, not where it merely sits — `core/run tools/wos/session/reads` ranks that.
<!-- norms:end -->

Git Flow, the branch gate's scope, the `--no-verify` protocol, and the push policy:
[`code/SPECS-git.md`](code/SPECS-git.md). *Gated by `core/hooks/git/gitflow_gate.py`.*
What the hooks block, and the contract a new agent's shim must satisfy:
[`core/hooks/SPECS.md`](core/hooks/SPECS.md). Installing the toolchain they need — stubgen, tsc,
caveman, rtk: [SETUP.md](SETUP.md).
What we intend to build: [`ROADMAP.md`](ROADMAP.md). What is currently untrue that we know about —
open issues, the entropy findings, the last verification result: [`ISSUES.md`](ISSUES.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`code/`](code/CONTEXT.md) | Software projects developed under this workspace |
| [`core/`](core/CONTEXT.md) | Agent library: skills, agents, prompts, flows, tools. Provider-agnostic. |
<!-- routing:end -->
