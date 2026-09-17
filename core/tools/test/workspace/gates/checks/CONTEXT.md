# checks
> Coverage for `core/hooks/checks/`: the standalone blocking checks the commit and edit hooks run.

Two clusters, and each is the boundary that put it here. The heredoc gate and the interpreter-heredoc
bug share a runner — one is the rule, the other is the shell shape that walked past it. The
issues-gate trio shares `issues_gate_harness.py`, a throwaway repo carrying an `ISSUES.md`: the
duplication gate refused the second inline copy, which is why the harness exists at all.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`issues_gate_harness.py`](issues_gate_harness.py) | [`issues_gate_harness.pyi`](issues_gate_harness.pyi) | `repo_with`, `edit_issue`, `spec_file` | Shared harness for the issues-gate tests: a throwaway repo with an ISSUES.md, and the gate run over an Edit payload the way the hook protocol delivers it. One copy, two consumers — the duplication gate refused the second inline duplicate. |
| [`test_b20260904_an_interpreter_heredoc_writes_any_file_past_every_edit_gate.py`](test_b20260904_an_interpreter_heredoc_writes_any_file_past_every_edit_gate.py) | [`test_b20260904_an_interpreter_heredoc_writes_any_file_past_every_edit_gate.pyi`](test_b20260904_an_interpreter_heredoc_writes_any_file_past_every_edit_gate.pyi) | — | b20260904 regression — a write performed inside an interpreted heredoc body is seen. |
| [`test_b20260913_the_line_gate_weighs_the_blob_the_commit_carries.py`](test_b20260913_the_line_gate_weighs_the_blob_the_commit_carries.py) | [`test_b20260913_the_line_gate_weighs_the_blob_the_commit_carries.pyi`](test_b20260913_the_line_gate_weighs_the_blob_the_commit_carries.pyi) | — | b20260913 regression — the line gate weighs what git will COMMIT, not what sits on disk. |
| [`test_b4_gate_messages.py`](test_b4_gate_messages.py) | [`test_b4_gate_messages.pyi`](test_b4_gate_messages.pyi) | — | T0: a hook must speak on the channel its class is read on. Two mirrored rules, one subject. |
| [`test_b7_durable_bug_ids.py`](test_b7_durable_bug_ids.py) | [`test_b7_durable_bug_ids.pyi`](test_b7_durable_bug_ids.pyi) | — | B7 regression — a bug id is a durable id, and never borrowed. |
| [`test_heredoc_gate.py`](test_heredoc_gate.py) | [`test_heredoc_gate.pyi`](test_heredoc_gate.pyi) | `run` | T0 the heredoc gate: a shell write to a workspace file must not walk past the file gates. |
| [`test_issues_gate_removal.py`](test_issues_gate_removal.py) | [`test_issues_gate_removal.pyi`](test_issues_gate_removal.pyi) | — | Regression — the issues gate reads removals, not only FIXED flips. |
<!-- routing:end -->
