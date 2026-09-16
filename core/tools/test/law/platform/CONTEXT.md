# platform
> The platform boundary's coverage: the one module allowed to know what an operating system is, and
> the credential-tightness ruling that rides on it.

Split from [`../`](../CONTEXT.md) 2026-08-31 at the crowding signal, on a boundary the directory's own
head already names: the file-shape law (what a file is, what a name may be) is a different
responsibility from what machine this is. The regression spec for the token modes lives beside the
boundary tests because the ruling is about the boundary's answer, not about Google.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b11_token_modes.py`](test_b11_token_modes.py) | [`test_b11_token_modes.pyi`](test_b11_token_modes.pyi) | — | B11 regression — a credential file is written tight, by the writer, on every system. |
| [`test_b20260901_a_git_symlink_is_a_text_file_on_windows.py`](test_b20260901_a_git_symlink_is_a_text_file_on_windows.py) | [`test_b20260901_a_git_symlink_is_a_text_file_on_windows.pyi`](test_b20260901_a_git_symlink_is_a_text_file_on_windows.pyi) | — | b20260901 regression — no tracked file in this workspace is a git symlink. |
| [`test_b20260901_a_second_shell_tool_walks_past_every_read_gate.py`](test_b20260901_a_second_shell_tool_walks_past_every_read_gate.py) | [`test_b20260901_a_second_shell_tool_walks_past_every_read_gate.pyi`](test_b20260901_a_second_shell_tool_walks_past_every_read_gate.pyi) | — | b20260901 regression — the gates fire on a capability, not on a tool's name. |
| [`test_b20260901_a_source_file_is_crlf_in_a_tree_that_declares_lf.py`](test_b20260901_a_source_file_is_crlf_in_a_tree_that_declares_lf.py) | [`test_b20260901_a_source_file_is_crlf_in_a_tree_that_declares_lf.pyi`](test_b20260901_a_source_file_is_crlf_in_a_tree_that_declares_lf.pyi) | `eol_rows`, `declared_lf` | b20260901 regression — a file the tree declares LF is LF, in the index AND on this disk. |
| [`test_b20260901_one_answers_file_is_shared_by_two_operating_systems.py`](test_b20260901_one_answers_file_is_shared_by_two_operating_systems.py) | [`test_b20260901_one_answers_file_is_shared_by_two_operating_systems.pyi`](test_b20260901_one_answers_file_is_shared_by_two_operating_systems.pyi) | — | b20260901 regression — this machine's answers override the shared ones and never travel. |
| [`test_b20260902_nothing_forbids_a_test_from_dirtying_the_real_tree.py`](test_b20260902_nothing_forbids_a_test_from_dirtying_the_real_tree.py) | [`test_b20260902_nothing_forbids_a_test_from_dirtying_the_real_tree.pyi`](test_b20260902_nothing_forbids_a_test_from_dirtying_the_real_tree.pyi) | `fake_root` | b20260902 regression — the law that no test touches the real workspace is now checked. |
| [`test_platform_law.py`](test_platform_law.py) | [`test_platform_law.pyi`](test_platform_law.pyi) | — | T0/T1 the platform boundary: the one module allowed to know what an operating system is, and until now the only law module with no test of its own. |
<!-- routing:end -->
