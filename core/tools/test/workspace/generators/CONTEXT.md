# generators
> What the generators must produce, and what they must never produce. Mirrors `core/hooks/generators/`.

A generator writes an artifact and stages it, so its failures are **silent by construction** — it
exits 0 having written nothing, or having written the right thing in the wrong place. That is why
these tests ask *"what does this produce, and is it there?"* rather than watching for an exception.

Every case here is a bug that shipped. The JS declaration path emitted nothing **for years**, and
stubgen wrote into a mirror of its own path; neither ever failed loudly. Silent failure is the
failure mode this workspace actually has: [/ROADMAP.md](../../../../../ROADMAP.md).

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_api_column.py`](test_api_column.py) | [`test_api_column.pyi`](test_api_column.pyi) | What the routing table's API column may name (core/hooks/SPECS.md). Zero-token, runs in verify-fast. |
| [`test_b20260901_a_generator_writes_the_hosts_path_separator.py`](test_b20260901_a_generator_writes_the_hosts_path_separator.py) | [`test_b20260901_a_generator_writes_the_hosts_path_separator.pyi`](test_b20260901_a_generator_writes_the_hosts_path_separator.pyi) | b20260901-a-generator-writes-the-hosts-path-separator regression — a markdown link target is |
| [`test_b20260901_a_tracked_json_cannot_be_routed_to.py`](test_b20260901_a_tracked_json_cannot_be_routed_to.py) | [`test_b20260901_a_tracked_json_cannot_be_routed_to.pyi`](test_b20260901_a_tracked_json_cannot_be_routed_to.pyi) | b20260901 regression — a tracked file with no comment syntax still earns its routing row. |
| [`test_interface_generators.py`](test_interface_generators.py) | [`test_interface_generators.pyi`](test_interface_generators.pyi) | T0 interface-generator invariants: a generated stub must land beside its source, and a jsconfig.json must never pretend to be a build config. Both bugs this guards were silent — the JS declaration path exited 0 and emitted nothing for years (ROADMAP Batch B item 6). |
| [`test_part_table.py`](test_part_table.py) | [`test_part_table.pyi`](test_part_table.pyi) | A cut type's index table (core/SCHEMA.md § What a part publishes about itself). |
| [`test_routing_sync_bugs.py`](test_routing_sync_bugs.py) | [`test_routing_sync_bugs.pyi`](test_routing_sync_bugs.pyi) | T0 routing-generator invariants (ROADMAP Batch B item 1): four ways the CONTEXT.md routing table used to corrupt itself. Each bug here was found by eye in a live file, never by a check. |
| [`test_routing_table.py`](test_routing_table.py) | [`test_routing_table.pyi`](test_routing_table.pyi) | The routing table's generated columns (core/hooks/SPECS.md). Zero-token, runs in verify-fast. |
<!-- routing:end -->
