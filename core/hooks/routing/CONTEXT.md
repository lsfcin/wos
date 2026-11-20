# routing
> The CONTEXT.md routing-table generator, and the delimited-block writer every generator shares.

**This directory is not split**, and the boundary it would split on is what each module does to a document: reads it (`header`, `hoist`, `workspace_meta`, `workspace_scanner`) against writes into it (`blocks`, `context_synchronizer`, `norms`, `part_table`). Costed 2026-08-24 alongside `core/hooks/entropy/`, same verdict — the hop removes less table than it adds, and a new directory is a `CONTEXT.md` the whole tree pays to read.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What the routing generator writes into an authored document, and where every file's one-line description has to come from. |
| [`blocks.py`](blocks.py) | [`blocks.pyi`](blocks.pyi) | `markers`, `line_pos`, `replace_block`, `main` | A generated block inside an authored file: found by its markers, rewritten in place. |
| [`context_synchronizer.py`](context_synchronizer.py) | [`context_synchronizer.pyi`](context_synchronizer.pyi) | `replace_block`, `sync_parts`, `sync` | Sync the Routing block in CONTEXT.md (or AGENTS.md at workspace root). |
| [`header.py`](header.py) | [`header.pyi`](header.pyi) | `header_fields` | The `> key: value` header a document declares itself with, parsed once for everyone who reads it. |
| [`hoist.py`](hoist.py) | [`hoist.pyi`](hoist.pyi) | `md_blurb`, `comment_paragraph`, `rebase_links`, `truncate_outside_links`, `hoist` | Text written for one file, made safe to show inside another file's table. |
| [`norms.py`](norms.py) | [`norms.pyi`](norms.pyi) | `body`, `published`, `block`, `sync` | Publish core/norms/*.md into AGENTS.md's rule block, in the registry's order. |
| [`part_table.py`](part_table.py) | [`part_table.pyi`](part_table.pyi) | `part_facts`, `render_table`, `parts_of`, `index_for`, `item_headlines` | A cut type's index table: what each TYPE-<name>.md publishes, rendered so the index answers "open or skip" without anything being opened. |
| [`workspace_meta.py`](workspace_meta.py) | [`workspace_meta.pyi`](workspace_meta.pyi) | `file_description`, `python_api`, `js_api`, `extract_api`, `interface_for` | Workspace metadata extraction: file descriptions, public APIs, and interface links. |
| [`workspace_scanner.py`](workspace_scanner.py) | [`workspace_scanner.pyi`](workspace_scanner.pyi) | `is_scanned`, `carried`, `code_files`, `has_code_content`, `subdir_scan` | Workspace scanner: directory discovery and CONTEXT.md routing-table assembly. |
<!-- routing:end -->
