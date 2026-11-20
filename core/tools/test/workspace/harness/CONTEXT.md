# harness
> The suite's own preconditions: nothing about the workspace, everything about the runner.

Split from [`../`](../CONTEXT.md) 2026-08-19 at the crowding signal, and the cut is a real one rather than a way to get under a number. Every other test here asks whether the **workspace** is in order;
these two ask whether the **suite** can be believed when it answers. A test that runs under a lying `sys.path` or a lying environment reports on something other than what it names, so these run before any conclusion drawn from the rest is worth anything.

Both exist because of an incident, and both incidents were silent:

- [`test_import_paths.py`](test_import_paths.py) — the suite's `sys.path` can shadow a module, so a test passes against the wrong copy of the code it claims to cover.
- [`test_hook_environment.py`](test_hook_environment.py) — a git hook exports `GIT_DIR` and `GIT_INDEX_FILE`, and every child inherits them. Under those, a fixture repo silently becomes the workspace repo: 19 tests failed only when `verify:fast` ran as a gate, and one fixture's `git add` replaced the real index. Found 2026-08-19.

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_hook_environment.py`](test_hook_environment.py) | [`test_hook_environment.pyi`](test_hook_environment.pyi) | T0 harness invariant: the suite must mean the same thing run by hand and run by a git hook. Zero-token, verify-fast. |
| [`test_import_paths.py`](test_import_paths.py) | [`test_import_paths.pyi`](test_import_paths.pyi) | T0 harness invariant: the suite's sys.path cannot silently shadow a module. |
<!-- routing:end -->
