# Workspace Root
> Canonical workspace entrypoint. Read before any task.

<!-- norms:start -->
- FILESYSTEM = source of truth. No memory, no assumptions.
- **PROVIDER-AGNOSTIC STORAGE**: the workspace owns its state, never a harness; if it insists, symlink the path into WIS.
- A LINK HANDED OUT GETS A NAME — `core/run tools/links/cfpages`, or `--short-name` where it is created.
Targets live in [`core/tools/links/links.txt`](core/tools/links/links.txt); a doc quotes the short link, never the mapping.
- **SECRETS STAY OUT OF GIT**: passwords, tokens, CPF/CNPJ go in a gitignored `<subtree>/segredos.env`; the text keeps the label.
- IMPROVE WOS, after finishing MICRO (particular task), take a step back and review and refine MACRO (structure). if it ain't feasible to do it on this session, WRITE IT DOWN IN THE REPO THAT OWNS IT: a defect in its `ISSUES.md`, work in its `ROADMAP.md`, tagged `[src: agent YYYY-MM-DD]`. `brain/INBOX.md` is Lucas's capture, never an agent's.
- DON'T ASSUME, always interview user to clarify his idea, intent, and design choices (about text, semantics, code, visuals, and structure). Agent acts as an opinionated expert, Lucas decides. Before a set of choices reaches him, an outside panel of domain experts (another vendor's model: `core/run tools/panel/ask`) comments, and its verdict sits next to each option. What he approves is shown in the chat or question text, never only in a popup `preview` — the VS Code popup does not render it, and text between tool calls may be invisible, so crucial questions and context belong in the last message of the turn.
- EXPAND ACRONYMS on first use. Aliases: [`core/SCHEMA.md`](core/SCHEMA.md) § Vocabulary.
- PLAIN WORD OVER JARGON: most precise wins, simpler breaks the tie, and a word survives only if the sentence reads worse without it. ONE IDEA, ONE WORD. A replaced word gets a row in [`core/SCHEMA.md`](core/SCHEMA.md) § Retired tokens, which is what finishes the rename. CHAT WITH LUCAS IN PT-BR (ruled 2026-11-16); files keep their tree's language.
- EDIT > CREATE: improve existing files, except for prototyping. Preserve documents authored by others: work in a separate file unless Lucas explicitly authorizes editing the original. Lucas-authored documents may be edited even when shared.
- A FILE OVER THE CAP IS CUT, NOT SPLIT. A `TYPE-<name>.md` sibling is a last resort, and Lucas's explicit OK. Reflowing is not cutting (ruled 2026-08-31): a file is held to lines AND to characters, so reshaping the same words satisfies neither — the way out is deleting.
- SYMMETRY IS A CORE VALUE, semantic and structural. When you find an asymmetry, write it down.
- **DONE WORK IS DELETED. GIT IS THE HISTORY.** No strikethrough, no annotated dead items.
- USE OUR TOOLS: we want those to be useful and perfected.
- REDUCING IS THE WAY: improve/extend by cutting size; growing the workspace takes Lucas's OK first.
Cut where a line is READ, not where it merely sits — `core/run tools/wos/session/reads` ranks that.
A weak feature is deleted whole, leaving one rejection note in its SPECS; while a design is still open, every variant stays until Lucas picks.
<!-- norms:end -->

Git flow, the branch lock, the close, the `--no-verify` protocol, and the push policy:
[`core/hooks/git/SPECS.md`](core/hooks/git/SPECS.md). *Enforced by `core/hooks/git/lock.py`.*
What the hooks block, and the contract a new agent's shim must satisfy:
[`core/hooks/SPECS.md`](core/hooks/SPECS.md). Installing the toolchain they need — stubgen, tsc, caveman, rtk: [SETUP.md](SETUP.md).
What we intend to build: [`ROADMAP.md`](ROADMAP.md). What is currently untrue that we know about —
open issues, the entropy findings, the last verification result: [`ISSUES.md`](ISSUES.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`code/`](code/CONTEXT.md) | Software projects developed under this workspace |
| [`core/`](core/CONTEXT.md) | Agent library: skills, agents, prompts, flows, tools. Provider-agnostic. |
<!-- routing:end -->
