# diagram
> The workspace drawn from its own declarations: one generated HTML picture, zero tokens, no model.

`architecture` writes [`ARCHITECTURE.html`](../../../../ARCHITECTURE.html) at the workspace root.
Everything above the tab strip answers *is it well tied, what is loose*; the tabs hold the detail
that answers *where exactly*. Every view reads a source that already exists:

| View | Renders | Read from |
|------|---------|-----------|
| summary | each declared layer against how hard it pushes, plus the findings and their targets | [`core/features.txt`](../../../features.txt) |
| lifecycle | which features fire at which moment of a session, in order | the hook registrations, via [`core/hooks/trigger/`](../../../hooks/trigger/CONTEXT.md) |
| fan-in | how many features one switch point carries | [`core/features.txt`](../../../features.txt) § wired |
| enforcement | every feature against every site that enforces it | [`core/features.txt`](../../../features.txt) |
| routing | the chain an agent walks, three levels deep | the generated routing blocks |
| mass | tracked bytes per directory | `git ls-files` |

**A hand-drawn map is the rot the routing tables exist to prevent**, so nothing here is drawn by
hand and no model runs at render time. The picture can be no more wrong than its sources: a wrong
edge means a wrong routing table, and fixing the drawing means fixing the source. **Nothing on the
page is inferred, as of 2026-08-18** — *when a hook fires* was the last exception, guessed from
directory convention until [`trigger_law.py`](../../../hooks/trigger/trigger_law.py) started reading
it out of the registrations. What the registrations cannot place is counted as a gap rather than
guessed at.

Total and fail-loud: every run prints `parsed N of M routing blocks`, and a block it cannot slice
is named rather than skipped — a picture that quietly drops a folder is worse than no picture.

```
core/run tools/wos/diagram/architecture              # regenerate ARCHITECTURE.html
core/run tools/wos/diagram/architecture --check      # exit 1 if the committed file is stale
core/run tools/wos/diagram/architecture --out /tmp/x.html
```

**There is one picture, and it is the workspace's.** A nested repo gets none, and asking for one is
a settled no: only *routing* and *mass* have a per-repo source, which is two drawings — too little
page to be worth opening. Revisit only if texpace/spacemantics gives a repo more to declare.

`/roundup` regenerates and commits it at every session close, which is what keeps a stale picture a
bug in the close rather than a fact of life. Output determinism is load-bearing for that: no
timestamp, no commit sha, so the file changes only when the workspace did.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`views/`](views/CONTEXT.md) | One drawing per file. A view renders data it is handed and computes nothing about the workspace. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`architecture`](architecture) | — | — | draw the workspace as it is (enforcement matrix, routing spine, folder mass) into one self-contained ARCHITECTURE.html; --check exits 1 when the committed file is stale |
| [`diagram_data.py`](diagram_data.py) | [`diagram_data.pyi`](diagram_data.pyi) | `area_of`, `trigger_of`, `lifecycle`, `features`, `matrix` | The canonical data behind ARCHITECTURE.html: what the workspace declares, what contains what, and how much of it there is. |
| [`diagram_footer.py`](diagram_footer.py) | [`diagram_footer.pyi`](diagram_footer.pyi) | `render` | The page's honesty block: what this picture covered, what it inferred, and where to change it. |
| [`diagram_health.py`](diagram_health.py) | [`diagram_health.pyi`](diagram_health.pyi) | `harness_owned`, `orphans`, `by_layer`, `findings`, `detail` | What the workspace's declarations say about its HEALTH, as opposed to its contents. |
| [`diagram_page.py`](diagram_page.py) | [`diagram_page.pyi`](diagram_page.pyi) | `render` | The page the three drawings live in: one self-contained HTML file, no script, no asset it does not carry. It opens from a file:// path on a machine with no network and under any provider, which is what "an asset inside the workspace" has to mean to be worth committing. |
<!-- routing:end -->
