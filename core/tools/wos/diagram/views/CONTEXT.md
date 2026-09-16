# views
> One drawing per file. A view renders data it is handed and computes nothing about the workspace.

Split from [`../`](../CONTEXT.md) 2026-08-18, when a fourth drawing passed the crowding signal. Every
module here takes values computed by [`diagram_data.py`](../diagram_data.py) or
[`diagram_health.py`](../diagram_health.py) and returns HTML. **A view that reads a file has
crossed the line** — it becomes a second place the workspace is measured, free to disagree with the
first, which is the failure the picture exists to make visible.

Each exports `render(...)` for the drawing and `legend(...)` for the writing beneath it.
[`../diagram_page.py`](../diagram_page.py) composes them into one self-contained document and owns
the shared stylesheet, so a view ships class names rather than a `<style>` block.

**[`diagram_fanin.py`](diagram_fanin.py) is the dated exception** — three shapes of one drawing, and
two `render_*` names instead of one, because Lucas asked on 2026-08-18 to see every candidate at
real scale before cutting. Two of the three go when he picks, and this paragraph with them.

**Encoding is an evidence question, not a taste one.** Position and length beat area, which beats
colour and density ([`core/refs/REFS.md`](../../../../refs/REFS.md) § Tooling), so a view rendering a quantity as glyphs
to be counted has picked the weakest channel and
needs a reason.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`diagram_fanin.py`](diagram_fanin.py) | [`diagram_fanin.pyi`](diagram_fanin.pyi) | `render_graph`, `render_bars`, `legend` | The wiring fan-in: how many features one switch point carries, and which points carry the load. |
| [`diagram_lifecycle.py`](diagram_lifecycle.py) | [`diagram_lifecycle.pyi`](diagram_lifecycle.pyi) | `render`, `legend` | The lifecycle sequence: which features fire at which moment of a session, in the order they run. |
| [`diagram_matrix.py`](diagram_matrix.py) | [`diagram_matrix.pyi`](diagram_matrix.pyi) | `render`, `legend` | The enforcement matrix: every declared feature against every site that enforces it. |
| [`diagram_overview.py`](diagram_overview.py) | [`diagram_overview.pyi`](diagram_overview.pyi) | `render` | The summary layer: the two questions answered before any detail arrives. |
| [`diagram_spine.py`](diagram_spine.py) | [`diagram_spine.pyi`](diagram_spine.pyi) | `render`, `legend` | The routing spine: which directory routes to which, drawn from the auto-synced routing blocks. |
| [`diagram_treemap.py`](diagram_treemap.py) | [`diagram_treemap.pyi`](diagram_treemap.pyi) | `render`, `legend` | Folder mass: how much of the workspace each directory actually is, by tracked bytes. |
<!-- routing:end -->
