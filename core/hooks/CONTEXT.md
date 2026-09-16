# hooks
> The enforcement layer: git hooks, agent lifecycle hooks, and the Level 0 checks they run.

Wired globally via `core.hooksPath` ([`SETUP-clone.md`](../../SETUP-clone.md) § Git hook), so
`pre-commit` fires in **every** repo under this workspace, and by absolute path from
`.claude/settings.json` for the agent-side gates.

**The law lives in this root, not in any checker.** Each law module below reads its answer out of a
data file rather than holding one, and **a checker that restates any of them is the drift the
checkers exist to catch** — the incidents behind that rule are in [`SPECS.md`](SPECS.md), and why a
gate skipping `feature_law` is a finding is [`core/SPECS.md`](../SPECS.md) § AD-14. When a
switched-on feature fires is answered in [`trigger/`](trigger/CONTEXT.md).

**Shape.** Only the law modules, the stdin parser and the three entrypoints whose names git and
`.claude/settings.json` dictate stay at the root; everything else is a subdirectory with one
responsibility. Two axes before you route. `gates/`, `generators/` and `postedit/` hold fragments
`source`d by `pre-commit` / `post-edit.sh` and share its shell state; every other directory holds
standalone programs run by path. A gate exits non-zero and stops the commit or the edit; a
generator writes an artifact and stages it. `entropy/` does neither — it reports into
[`ISSUES.md`](../../ISSUES.md), so read that report instead of re-scanning the tree.

Gate behavior, the agent-shim contract, and how a module reaches the root law:
[`SPECS.md`](SPECS.md). Why the `code/` gates exist:
[`code/ROADMAP-verify.md`](../../code/ROADMAP-verify.md). Their toolchain: [`SETUP.md`](../../SETUP.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`antigravity/`](antigravity/CONTEXT.md) | Provider shim: translates Antigravity lifecycle events to canonical WOS gates. |
| [`brain/`](brain/CONTEXT.md) | brain/ attention stats and the GOALS.md dashboard. |
| [`checks/`](checks/CONTEXT.md) | Standalone blocking checks the commit and edit hooks run. |
| [`commit/`](commit/CONTEXT.md) | The git pre-commit and post-commit pipeline: what runs on every commit, in what order, and the one place a commit is refused. |
| [`compact/`](compact/CONTEXT.md) | Shrink tool output before it reaches the context — the input-side twin of caveman. |
| [`copilot/`](copilot/CONTEXT.md) | Provider shim: translates Copilot hook payloads onto the canonical gates. |
| [`entropy/`](entropy/CONTEXT.md) | The Level 0 checks that count what the tree has drifted into. One question each. |
| [`facade/`](facade/CONTEXT.md) | The facade discipline: read the facade before editing, never import around it. |
| [`git/`](git/CONTEXT.md) | Gates and self-heals about git state itself: branch shape, gitlinks, .gitignore. |
| [`postedit/`](postedit/CONTEXT.md) | Sourced post-edit stages: regenerate interfaces, remind, sync, lint. |
| [`read/`](read/CONTEXT.md) | Who must read what before touching a folder — and who gets handed it instead. |
| [`routing/`](routing/CONTEXT.md) | The CONTEXT.md routing-table generator, and the delimited-block writer every generator shares. |
| [`session/`](session/CONTEXT.md) | Session lifecycle: start, prune, precompact wipe, and the SessionStart nudges. |
| [`stubgen/`](stubgen/CONTEXT.md) | Interface stubs and paper scaffolding, generated on save and on commit. |
| [`trigger/`](trigger/CONTEXT.md) | When a feature fires, read from the registrations rather than from where its file sits. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What each gate blocks, what the hooks write, and the contract a new agent's shim must satisfy. |
| [`described.txt`](described.txt) | — | — | Files DESCRIBED HERE because they cannot describe themselves. One "<path><TAB><description>" per line, path relative to the workspace root. Read by core/hooks/routing/workspace_meta.py. |
| [`dispatch.py`](dispatch.py) | [`dispatch.pyi`](dispatch.pyi) | `table_path`, `load_table`, `run_gate`, `emit`, `collect` | PreToolUse, PostToolUse: one process for every gate — read stdin once, ask the moment and the capability once, run what they select. |
| [`extensionless.txt`](extensionless.txt) | — | — | Files allowed to have no extension because something OUTSIDE this workspace dictates the name — enforced by test_every_extensionless_tracked_file_is_explained. |
| [`feature_law.py`](feature_law.py) | [`feature_law.pyi`](feature_law.pyi) | `load_registry`, `names`, `load_profile`, `is_enabled`, `setting` | What is switched ON: which features are live. The registry is core/features.txt, the answers are core/profile.txt, and neither is restated here. |
| [`file_law.py`](file_law.py) | [`file_law.pyi`](file_law.pyi) | `is_tool_entrypoint`, `is_code_file`, `load_limits`, `allowed_extensionless`, `is_vendored` | What a file IS, and which rules apply to it. The numeric-law sibling of schema_law.py: that module parses core/SCHEMA.md, this one owns the file-shape law every size, crowding and line-count check reads. |
| [`gates.txt`](gates.txt) | — | — | Every lifecycle gate, the moment and the capability that select it. Read by core/hooks/dispatch.py (which runs them) and by core/hooks/trigger/trigger_law.py (which reports when they fire). |
| [`generated.txt`](generated.txt) | — | — | Files this workspace GENERATES, each entry naming its generator. Exempt from every authoring rule; what the exemption covers and why it is safe: core/hooks/SPECS.md § Generated artifacts. |
| [`gitignore-exceptions.txt`](gitignore-exceptions.txt) | — | — | One "<domain>/<dir>" per line: a CONTEXT.md-bearing subdir Lucas deliberately wants left out of the .gitignore allowlist (reviewed, not an oversight). gitignore-self-heal.sh skips any name listed here instead of re-adding its `!<domain>/<dir>/` line. |
| [`hook_input.py`](hook_input.py) | [`hook_input.pyi`](hook_input.pyi) | `parse_stdin`, `capability`, `is_subagent`, `normalise`, `store` | Shared parser for Claude Code hook stdin JSON — nested (current) and flat (legacy shim) schemas. |
| [`limits.env`](limits.env) | — | — | Every numeric limit in the workspace, in one file. Read through core/hooks/file_law.py, the one reader, by every gate and instrument that holds a file to a number — same file, one law. |
| [`platform_law.py`](platform_law.py) | [`platform_law.pyi`](platform_law.pyi) | `venv_script`, `interpreter`, `session_state`, `install_command`, `package_install` | The platform boundary: the one file in this workspace allowed to know what an operating system is. |
| [`post-commit`](post-commit) | — | — | auto-push feature/*. Same handoff as pre-commit beside it. Never blocks: git ignores a post-commit's exit status, and every failure here is a warning. |
| [`post-edit.sh`](post-edit.sh) | — | — | PostToolUse, capability `write` — regenerates interfaces, checks first-line comment, syncs CONTEXT.md |
| [`pre-commit`](pre-commit) | — | — | Workspace pre-commit hook. Applied globally: git config --global core.hooksPath <this directory> |
| [`schema_law.py`](schema_law.py) | [`schema_law.pyi`](schema_law.pyi) | `load_law`, `load_scopes`, `load_retired` | The law parser. Every Level 0 check reads core/SCHEMA.md through this module, and none of them restates it — a second copy of the law inside a checker is the exact drift the checks exist to catch. |
| [`scoreboard.py`](scoreboard.py) | [`scoreboard.pyi`](scoreboard.pyi) | `path`, `enabled`, `record`, `tally`, `started` | What each feature ACTUALLY did, counted at the moment it ran: how often it fired, and how often it blocked something real. The fourth question beside what a file IS, what a name MAY BE and which features are LIVE — those three read declarations, this one reads behaviour. |
| [`vendored.txt`](vendored.txt) | — | — | Third-party files we did not author, exempt from every authoring rule for the reason core/hooks/SPECS.md § Generated artifacts gives. |
<!-- routing:end -->
