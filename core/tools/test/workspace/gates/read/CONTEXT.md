# read
> Coverage for `core/hooks/read/`: who must read what before touching a folder, and who gets handed
> it instead.

A gate here and the tracker that clears it are one subject and are tested together on purpose —
b20260901 was a race between exactly those two, and a suite that filed them apart could not have
seen it. The bash arm belongs here for the same reason: the command is a way of reaching a file,
so what it must have read first is this directory's question, not the shell's.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_agent_context.py`](test_agent_context.py) | [`test_agent_context.pyi`](test_agent_context.pyi) | `prompt_id` | T0 the agent-context briefing (core/hooks/SPECS.md): the orchestrator's duty, done by a hook. |
| [`test_b20260901_a_read_gate_races_the_tracker_that_clears_it.py`](test_b20260901_a_read_gate_races_the_tracker_that_clears_it.py) | [`test_b20260901_a_read_gate_races_the_tracker_that_clears_it.pyi`](test_b20260901_a_read_gate_races_the_tracker_that_clears_it.pyi) | — | b20260901-a-read-gate-races-the-tracker-that-clears-it regression — a parallel batch of reads loses none of its marks. |
| [`test_bash_context_gate.py`](test_bash_context_gate.py) | [`test_bash_context_gate.pyi`](test_bash_context_gate.pyi) | — | T0 the bash context gate reads the COMMAND, never the text the command carries. Zero-token, runs in verify-fast. |
| [`test_read_gate_prerequisites.py`](test_read_gate_prerequisites.py) | [`test_read_gate_prerequisites.pyi`](test_read_gate_prerequisites.pyi) | — | T0: a blocking read gate names every prerequisite of the read, not the one it happens to own. |
| [`test_subagent_gate.py`](test_subagent_gate.py) | [`test_subagent_gate.pyi`](test_subagent_gate.pyi) | — | T0 the subagent exemption (core/hooks/SPECS.md): a worker is not made to read the routing chain. |
<!-- routing:end -->
