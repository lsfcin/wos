# workspace
> Level 0 workspace-wide invariants: pointers resolve, .gitignore self-heals, imports do not shadow.

Split 2026-08-15 at 8 files and again 2026-09-06 at 15. What stays is what holds for the **whole
tree** rather than for one piece of machinery: every relative link resolves, a new domain
subdirectory does not fall out of the `.gitignore` allowlist, and the suite's `sys.path` cannot
silently shadow a module.

Three subdirectories are named for the code they cover, so a surface and its coverage are one word
apart — [`gates/`](gates/CONTEXT.md), [`generators/`](generators/CONTEXT.md) and
[`shims/`](shims/CONTEXT.md). Two are named for a **question** instead, because no single directory
owns it: [`ratchets/`](ratchets/CONTEXT.md) asks whether the backlog is shrinking, and
[`harness/`](harness/CONTEXT.md) asks what the runner itself needs before any of this can run.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`gates/`](gates/CONTEXT.md) | What a blocking gate must say, and who it must fire for. One subdirectory per `core/hooks/` directory covered; what stays at this level belongs to no single one. |
| [`generators/`](generators/CONTEXT.md) | What the generators must produce, and what they must never produce. Mirrors `core/hooks/generators/`. |
| [`harness/`](harness/CONTEXT.md) | The suite's own preconditions: nothing about the workspace, everything about the runner. |
| [`ratchets/`](ratchets/CONTEXT.md) | Whether the backlog is shrinking — one ceiling per defect, and every ceiling only ever goes down. |
| [`shims/`](shims/CONTEXT.md) | The harness fleet: every provider's registration resolves, reaches the dispatcher, and declares itself in the one place the mirror list lives. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260901_a_bash_tool_costs_thirty_seconds_a_commit_here.py`](test_b20260901_a_bash_tool_costs_thirty_seconds_a_commit_here.py) | [`test_b20260901_a_bash_tool_costs_thirty_seconds_a_commit_here.pyi`](test_b20260901_a_bash_tool_costs_thirty_seconds_a_commit_here.pyi) | — | b20260901-a-bash-tool-costs-thirty-seconds-a-commit-here regression. |
| [`test_b20260902_core_run_reads_any_two_letters_sh_as_a_shebang.py`](test_b20260902_core_run_reads_any_two_letters_sh_as_a_shebang.py) | [`test_b20260902_core_run_reads_any_two_letters_sh_as_a_shebang.pyi`](test_b20260902_core_run_reads_any_two_letters_sh_as_a_shebang.pyi) | — | core/run runs what it says it runs: a bash target runs as bash, a python target reaches the interpreter, and a python target whose comment merely contains those two letters is still python. |
| [`test_b20260905_brain_drafts_carries_two_asymmetries.py`](test_b20260905_brain_drafts_carries_two_asymmetries.py) | [`test_b20260905_brain_drafts_carries_two_asymmetries.pyi`](test_b20260905_brain_drafts_carries_two_asymmetries.pyi) | `tracked`, `declared_subtrees` | b20260905 regression — a declared subtree is carried by git, and a model named in a filename is attribution rather than a directive. |
| [`test_b20260911_the_close_cannot_roll_back_a_file_git_has_never_seen.py`](test_b20260911_the_close_cannot_roll_back_a_file_git_has_never_seen.py) | [`test_b20260911_the_close_cannot_roll_back_a_file_git_has_never_seen.pyi`](test_b20260911_the_close_cannot_roll_back_a_file_git_has_never_seen.pyi) | — | b20260911 regression — settle() undoes a CREATE by deleting, not by checking out. |
| [`test_b20260911_the_publish_repo_carries_a_list_its_spec_forbids.py`](test_b20260911_the_publish_repo_carries_a_list_its_spec_forbids.py) | [`test_b20260911_the_publish_repo_carries_a_list_its_spec_forbids.pyi`](test_b20260911_the_publish_repo_carries_a_list_its_spec_forbids.pyi) | — | b20260911 regression — a repo the workspace PUBLISHES to keeps no findings of its own. |
| [`test_brain_attention.py`](test_brain_attention.py) | [`test_brain_attention.pyi`](test_brain_attention.pyi) | — | T0 the goal-file `>**owns**` block: a field ends where its block ends. Zero-token, verify-fast. |
| [`test_gitignore_self_heal.py`](test_gitignore_self_heal.py) | [`test_gitignore_self_heal.pyi`](test_gitignore_self_heal.pyi) | — | T0 self-healing .gitignore allowlist check (core/hooks/SPECS.md): a new domain subdir with a CONTEXT.md must get its `!<domain>/<dir>/` allow line added automatically, no human action. |
| [`test_pointer_integrity.py`](test_pointer_integrity.py) | [`test_pointer_integrity.pyi`](test_pointer_integrity.pyi) | `check_separators`, `check_pointers` | T0 pointer-integrity check (Level 0): every relative ](path) link across CONTEXT.md / ROADMAP*.md / SCHEMA.md / AGENTS.md (repo) and MEMORY.md (auto-memory) must resolve. Zero-token, runs in verify-fast. |
| [`test_projects_declaration.py`](test_projects_declaration.py) | [`test_projects_declaration.pyi`](test_projects_declaration.pyi) | `declared_in_gitignore`, `listed_in_projects` | T0 the project map (core/SCHEMA.md § The .md type system): every internal project is declared, and the declaration cannot drift from the one place git already names them. |
| [`test_setup_executable.py`](test_setup_executable.py) | [`test_setup_executable.pyi`](test_setup_executable.pyi) | — | T0 the install is a procedure, not prose (core/SCHEMA.md § The .md type system): every SETUP.md step declares its feature and carries a precondition, an install and a verify check. |
<!-- routing:end -->
