# ratchets
> Whether the backlog is shrinking — one ceiling per defect, and every ceiling only ever goes down.

These answer a different question from the checks they call. `law/entropy/` owns whether each check
**fires correctly**; these own whether the tree is **carrying less of what it finds** than it was.
That is why a ceiling is paired with a staleness test in each file: a ratchet nobody lowers is just
a baseline, and a baseline is where drift hides.

One ceiling per defect, never one shared. Until 2026-08-15 the placeholder marker was counted as
finished-work writing, so seventy markers could have masked seventy new dead items without the number
moving.

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_b20260905_a_timing_assertion_fails_under_the_load_the_suite_itself_creates.py`](test_b20260905_a_timing_assertion_fails_under_the_load_the_suite_itself_creates.py) | [`test_b20260905_a_timing_assertion_fails_under_the_load_the_suite_itself_creates.pyi`](test_b20260905_a_timing_assertion_fails_under_the_load_the_suite_itself_creates.pyi) | b20260905 regression — no case in this suite decides anything by reading a clock. |
| [`test_corpus_ratchet.py`](test_corpus_ratchet.py) | [`test_corpus_ratchet.pyi`](test_corpus_ratchet.pyi) | T0 corpus ratchets (core/SCHEMA.md § Placement): the .md corpus may not accumulate more of the three defects no link-checker can see. Zero-token, runs in verify-fast. |
| [`test_encoding_ratchet.py`](test_encoding_ratchet.py) | [`test_encoding_ratchet.pyi`](test_encoding_ratchet.pyi) | T0 the encoding law: no text read or write in this workspace inherits the operating system's answer. Zero-token, runs in verify-fast. |
| [`test_port_ratchet.py`](test_port_ratchet.py) | [`test_port_ratchet.pyi`](test_port_ratchet.pyi) | T0 the OS-agnostic port's invariants (AD-0): the tree may not re-acquire the defects the port removed. Zero-token, runs in verify-fast. |
<!-- routing:end -->
