# diagram
> Coverage for the workspace picture, split the way its source is: what it draws, and what it claims.

Split from [`../`](../CONTEXT.md) 2026-08-18, when the parent hit the crowding signal — the same mirroring rule [`../../law/entropy/`](../../law/entropy/CONTEXT.md) follows, so the file testing a surface is found by knowing the name of the surface.

**Two questions, and they fail differently.** [`test_diagram.py`](test_diagram.py) asks whether the picture can be more wrong than its sources: a source silently dropped so the drawing looks complete while a folder is missing, or an inferred edge drawn like a declared one.
[`test_diagram_health.py`](test_diagram_health.py) asks whether a number the page presents as a **problem** actually is one.

That second file exists because of a real defect rather than a hypothetical. The findings list opened with *"28 of 68 features enforce nothing"* — which counted the skills, tools and recording hooks that wait to be called instead of pushing, and reported the workspace's capability layer as dead weight. **A findings list whose biggest number is not a problem teaches its reader to stop believing the rest of it**, so the regression is pinned here rather than left to review.

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_diagram.py`](test_diagram.py) | [`test_diagram.pyi`](test_diagram.pyi) | T1 the workspace picture: the generator behind ARCHITECTURE.html. Zero-token, no network, no browser. |
| [`test_diagram_health.py`](test_diagram_health.py) | [`test_diagram_health.pyi`](test_diagram_health.pyi) | T1 the workspace's health reading: the findings behind the summary layer, and the grid that draws them. Zero-token, no network, no browser. |
<!-- routing:end -->
