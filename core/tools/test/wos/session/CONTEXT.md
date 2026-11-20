# session
> The instruments: what a session costs, what fills its window, and what a read was served.

Mirrors [`core/tools/wos/session/`](../../../wos/session/CONTEXT.md), so a surface and its coverage are one word apart — the same split [`workspace/`](../../workspace/CONTEXT.md) made into `gates/` and `generators/`.

Split out 2026-08-17, when `wos/` crossed the crowding signal. What stayed above is **declaration** —
whether the registry, the profile and `deps.txt` agree, and whether the session-close ritual does what its skill says. What moved here is **measurement**: these read real transcripts and answer in numbers, which is a different job and a different failure mode. A declaration test fails when two files disagree; an instrument test fails when the number is quietly wrong, which is the failure the ablation exists to catch.

Zero-token, no network. Fixtures are built per test; nothing reads Lucas's real transcripts.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260905_the_cost_line_prices_every_session_at_opus_rates.py`](test_b20260905_the_cost_line_prices_every_session_at_opus_rates.py) | [`test_b20260905_the_cost_line_prices_every_session_at_opus_rates.pyi`](test_b20260905_the_cost_line_prices_every_session_at_opus_rates.pyi) | `response`, `project` | b20260905 regression — the cost line believes the model stamp only when the record proves it. |
| [`test_context.py`](test_context.py) | [`test_context.pyi`](test_context.pyi) | `turn`, `result`, `use`, `transcript` | T1 the context instrument (core/hooks/SPECS.md): what fills the window, attributed from the transcript. |
| [`test_reads.py`](test_reads.py) | [`test_reads.pyi`](test_reads.pyi) | `transcript`, `read_pair` | T1 the read instrument: a Read costs what it was SERVED, and a stub is not a source. |
| [`test_trace.py`](test_trace.py) | [`test_trace.pyi`](test_trace.pyi) | `response`, `spawn`, `call`, `project` | T1 the trace instrument: who a session spawned, where its clock went, and what came back loudest. |
| [`test_usage.py`](test_usage.py) | [`test_usage.pyi`](test_usage.pyi) | `response`, `text`, `thinking`, `project` | T1 the cost instrument: what counts as one turn, and which half of output is re-read. |
<!-- routing:end -->
