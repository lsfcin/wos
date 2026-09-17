# Code
> Software projects developed under this workspace
> spec: none

You are a SENIOR software architect, your code WILL be evaluated!

**Before editing any file:** read it first, grep for every caller before changing a function, and
read the facade (`index.ts` / `__init__.py`) of every module you will touch.

**You enforce this — no hook can:**
- REUSE always. NEVER copy-paste: refactor, extract a function or class.
- ONE responsibility per file — SMALL IS BETTER.
- REFACTOR after each coding prompt, and report only *after* refactoring.
- Names must be guessable without reading files, functions, or inspecting variables.

**Language rules, file templates, and the R1–R6 style table:** [SPECS-style.md](SPECS-style.md) § Style Rules (R1-R6).

**Git Flow**, the branch gate's scope, and the push policy: [SPECS-git.md](SPECS-git.md).

**Hooks block automatically** — each explains itself and names the fix when it fires, so nothing
about them is restated here. Every numeric limit lives in `core/hooks/limits.env`, and a copy of one
here went five days stale before it was deleted. Reasoning: [ROADMAP-verify.md](ROADMAP-verify.md).

**New project**: needs `CONTEXT.md` + `README.md`. Templates: [`_templates/`](_templates/).

**CONTEXT.md files**: line 2 = `> description`, line 3 = `> spec:` for a module. The routing block
is auto-managed — never edit it by hand.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`_templates/`](_templates/CONTEXT.md) | Project scaffolding templates — CONTEXT.md, README.md, SPECS.md, ROADMAP.md skeletons |
| [`aiwbot/`](aiwbot/CONTEXT.md) | Provider-agnostic bot: control swappable coding agents (claude·opencode·copilot) from chat. |

| File | API | Description |
|------|-----|-------------|
| [`SETUP.md`](SETUP.md) | — | Per-language setup, facade templates, and project scaffolding reference |
| [`SPECS-git.md`](SPECS-git.md) | — | Which branches exist, what may be committed where, and when work is pushed. |
| [`SPECS-structure.md`](SPECS-structure.md) | — | How a project is laid out: its files, its module specs, and its facade. |
| [`SPECS-style.md`](SPECS-style.md) | — | How a file is written, how big it may get, and when a directory splits. |
| [`SPECS.md`](SPECS.md) | — | Engineering conventions, architecture decisions, and process rules for all code/ projects. |
| [`eslint.shared.js`](eslint.shared.js) | `localPlugin`, `sharedRules`, `countCallsInSubtree`, `getChainDepth` | Shared ESLint rules for all TypeScript/JavaScript projects under code/ — R1-R6 style enforcement. |
<!-- routing:end -->
