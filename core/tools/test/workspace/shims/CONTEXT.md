# shims
> The harness fleet: every provider's registration resolves, reaches the dispatcher, and declares
> itself in the one place the mirror list lives.

Coverage for `core/hooks/copilot/`, `core/hooks/antigravity/`, the `.opencode/` plugin and each
harness's own registration file — plus `core/harnesses.txt`, which is the declaration all of them
are checked against.

**What these prove is that a path RESOLVES, never that a gate FIRES.** Said plainly because this
workspace's own rule is that a check proving a name is present is the weaker kind. Every failure
this directory has ever caught was the same shape and none of it was behavioural: a shim pointing
at a script that had moved, a registration spelling an interpreter it should have asked for, a
mirror list kept in a bash array. Each was invisible precisely because the coverage was claimed in
a table rather than read by anything.

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_antigravity_shim.py`](test_antigravity_shim.py) | [`test_antigravity_shim.pyi`](test_antigravity_shim.pyi) | T0: Antigravity provider shim unit test suite. |
| [`test_b13_harness_declaration.py`](test_b13_harness_declaration.py) | [`test_b13_harness_declaration.pyi`](test_b13_harness_declaration.pyi) | B13 regression — the harness mirror list is declared once, in a data file something reads. |
| [`test_b20260905_a_ratchet_that_greps_one_file_type_misses_the_config_that_broke_it.py`](test_b20260905_a_ratchet_that_greps_one_file_type_misses_the_config_that_broke_it.py) | [`test_b20260905_a_ratchet_that_greps_one_file_type_misses_the_config_that_broke_it.pyi`](test_b20260905_a_ratchet_that_greps_one_file_type_misses_the_config_that_broke_it.pyi) | b20260905 regression — a registration is a registration whatever file type it lives in. |
| [`test_b5_zcode_check_registrations_removed.py`](test_b5_zcode_check_registrations_removed.py) | [`test_b5_zcode_check_registrations_removed.pyi`](test_b5_zcode_check_registrations_removed.pyi) | T0 B5 regression — the zcode check instruments are out and stay out. Zero-token, verify-fast. |
| [`test_shim_paths.py`](test_shim_paths.py) | [`test_shim_paths.pyi`](test_shim_paths.pyi) | T0 the shim contract (core/hooks/SPECS.md): every canonical script a provider shim spawns must exist. Zero-token, verify-fast. |
<!-- routing:end -->
