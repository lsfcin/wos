# entropy
> What each entropy check counts, and where it must stay silent. **One file per check, not one per
> module** — so a name here answers to a question, and only sometimes to a file next door.

Split from `law/` 2026-08-15, one word apart from the surface it covers — and that naming holds only where a module IS one check (ruled 2026-08-25, after `ISSUES.md` carried the shortfall as a bug for calling this a mirror it never was). `entropy_list.py` and `entropy_context.py` each answer several questions, so `inventory`, `placeholders` and `retired` are named for the check. `entropy_corpus.py` and `entropy_size.py` have no file because neither is a check — one picks the files the others may look at, the other measures what they find — so both are reached through the tests importing them.

These own whether each check **fires correctly**, and the boundaries are the design: every one is a case where two things look identical and mean opposite things — a tick is a dead item in a list and a legend marker in a spec. Whether the **backlog is shrinking** is a different question, owned by the ceilings in [`../../workspace/`](../../workspace/CONTEXT.md).

Write the glyphs these checks hunt for **only inside a test**, never in this head: the checks read writing literally, and a `CONTEXT.md` quoting a marker is indistinguishable from one that never answered it — to the check and to a reader skimming it. That is not a false positive to exempt away;
it is the same ambiguity the reader has.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`dashboard/`](dashboard/CONTEXT.md) | The checks that are about the REPORT rather than about the tree: what a list may claim, and what the count was last time. |

| File | Interface | Description |
|------|-----------|-------------|
| [`test_entropy_context.py`](test_entropy_context.py) | [`test_entropy_context.pyi`](test_entropy_context.pyi) | T0 CONTEXT.md rules (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast. |
| [`test_entropy_crowding.py`](test_entropy_crowding.py) | [`test_entropy_crowding.pyi`](test_entropy_crowding.pyi) | T0 directory crowding (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast. |
| [`test_entropy_fields.py`](test_entropy_fields.py) | [`test_entropy_fields.pyi`](test_entropy_fields.pyi) | T0 the header-field check (core/SCHEMA.md § Every field that names our own code is verified): a field naming our own code names something that is there. Zero-token, runs in verify-fast. |
| [`test_entropy_inventory.py`](test_entropy_inventory.py) | [`test_entropy_inventory.pyi`](test_entropy_inventory.pyi) | T0 no-hand-inventory rule (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast. |
| [`test_entropy_list.py`](test_entropy_list.py) | [`test_entropy_list.pyi`](test_entropy_list.pyi) | T0 list and vocabulary checks (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast. |
| [`test_entropy_naming.py`](test_entropy_naming.py) | [`test_entropy_naming.pyi`](test_entropy_naming.pyi) | T0 naming and placement (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast. |
| [`test_entropy_placeholders.py`](test_entropy_placeholders.py) | [`test_entropy_placeholders.pyi`](test_entropy_placeholders.pyi) | T0 unanswered placeholders (first-line-comment rule, core/hooks/SPECS.md). Zero-token, runs in verify-fast. |
| [`test_entropy_retired.py`](test_entropy_retired.py) | [`test_entropy_retired.pyi`](test_entropy_retired.pyi) | T0 the retired-token check (core/SCHEMA.md § Retired tokens): a rename is finished only when its old spelling appears nowhere. Zero-token, runs in verify-fast. |
| [`test_entropy_stores.py`](test_entropy_stores.py) | [`test_entropy_stores.pyi`](test_entropy_stores.pyi) | T0 the two doubt stores (core/SPECS.md § AD-16 band 1): an experiment states its own format, and a judged reference carries a source level. Zero-token, runs in verify-fast. |
| [`test_entropy_vendor.py`](test_entropy_vendor.py) | [`test_entropy_vendor.pyi`](test_entropy_vendor.pyi) | T0 the vendor-name guard (core/SCHEMA.md): a list assigns a LEVEL, never a model. Zero-token, runs in verify-fast. |
<!-- routing:end -->
