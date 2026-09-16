# gates
> What a blocking gate must say, and who it must fire for. One subdirectory per `core/hooks/`
> directory covered; what stays at this level belongs to no single one.

Split 2026-09-06 at 21 files, which **retires the mismatch this head used to declare**: the name
said `core/hooks/gates/` and the contents were `read/`, `checks/`, `git/` and `compact/` as well.
Each subdirectory is now named for the hook directory it covers — the shape `law/entropy/` and
`generators/` already have — and the exception is spelled out in [`vcs/`](vcs/CONTEXT.md)'s own head.

What stays here crosses all of them: the two `stubgen/` cases, the facade set, the bash-compaction
shim, and the two b20260905 cases that ask what EVERY registration costs rather than what one gate
does.

The questions here are independent, which is why they are separate files: a hook can block the right
agent for the wrong reason, the wrong agent with a perfect message, or rewrite shell it had no
business touching.

Why each one exists, and the one place a test reads source instead of running it: [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`checks/`](checks/CONTEXT.md) | Coverage for `core/hooks/checks/`: the standalone blocking checks the commit and edit hooks run. |
| [`read/`](read/CONTEXT.md) | Coverage for `core/hooks/read/`: who must read what before touching a folder, and who gets handed it instead. |
| [`vcs/`](vcs/CONTEXT.md) | Coverage for `core/hooks/git/`: branch shape, push diagnosis, and the mirror a pull leaves stale. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | Why each hook test exists, and the one structural exception to running the real hook. |
| [`test_b20260831_silent_stub_gate.py`](test_b20260831_silent_stub_gate.py) | [`test_b20260831_silent_stub_gate.pyi`](test_b20260831_silent_stub_gate.pyi) | — | b20260831-silent-stub-gate regression — a gate that is OFF must say so. |
| [`test_b20260901_the_codegraph_nudge_only_fires_when_a_stub_is_stale.py`](test_b20260901_the_codegraph_nudge_only_fires_when_a_stub_is_stale.py) | [`test_b20260901_the_codegraph_nudge_only_fires_when_a_stub_is_stale.pyi`](test_b20260901_the_codegraph_nudge_only_fires_when_a_stub_is_stale.pyi) | `indexed_project` | b20260901-the-codegraph-nudge-only-fires-when-a-stub-is-stale regression — a suggestion about the PROJECT fires for the project, not for the one file whose stub happens to be out of date. |
| [`test_b20260901_the_facade_set_is_written_out_in_four_places.py`](test_b20260901_the_facade_set_is_written_out_in_four_places.py) | [`test_b20260901_the_facade_set_is_written_out_in_four_places.pyi`](test_b20260901_the_facade_set_is_written_out_in_four_places.pyi) | — | b20260901-the-facade-set-is-written-out-in-four-places regression — what a file IS has one home. |
| [`test_b20260905_every_tool_call_now_pays_for_every_gate.py`](test_b20260905_every_tool_call_now_pays_for_every_gate.py) | [`test_b20260905_every_tool_call_now_pays_for_every_gate.pyi`](test_b20260905_every_tool_call_now_pays_for_every_gate.pyi) | `rows`, `run`, `call`, `with_table`, `declare` | b20260905 regression — one process asks the capability question once, and answers it the way nine processes did. |
| [`test_b20260905_hooks_and_tools_suspected_of_paying_more_time_than_needed.py`](test_b20260905_hooks_and_tools_suspected_of_paying_more_time_than_needed.py) | [`test_b20260905_hooks_and_tools_suspected_of_paying_more_time_than_needed.pyi`](test_b20260905_hooks_and_tools_suspected_of_paying_more_time_than_needed.pyi) | `configs`, `registrations` | b20260905 regression — a lifecycle hook pays for the moment it serves, and for no other. |
| [`test_b20260912_a_gate_reads_a_name_the_law_does_not_allow.py`](test_b20260912_a_gate_reads_a_name_the_law_does_not_allow.py) | [`test_b20260912_a_gate_reads_a_name_the_law_does_not_allow.pyi`](test_b20260912_a_gate_reads_a_name_the_law_does_not_allow.pyi) | — | b20260912 regression — two gates recognised a shape by a spelling of their own instead of by the law, and both refused correct code. Found when code/aiwbot was absorbed into this repo and its 261 files met these gates for the first time. |
| [`test_bash_compact_rewrite.py`](test_bash_compact_rewrite.py) | [`test_bash_compact_rewrite.pyi`](test_bash_compact_rewrite.pyi) | `rtk_path` | T0 the multi-line rtk shim: it must reach lines 2+, and must never reshape shell it cannot read. |
| [`test_memory_gate.py`](test_memory_gate.py) | [`test_memory_gate.pyi`](test_memory_gate.pyi) | `run` | T0 the memory gate: a memory is written when Lucas asks for one, and the switch is what says so. |
<!-- routing:end -->
