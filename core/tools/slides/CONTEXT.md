# slides
> Presentations, read and edited in place. Provider leaf: `gslides` (Google Slides API).

```bash
core/run tools/slides/gslides list  --account personal --name "AI4Good"
core/run tools/slides/gslides read  --account personal <presentation_id>     # deck as navigable text
core/run tools/slides/gslides new   --account personal "Aula 3"
core/run tools/slides/gslides text  --account personal --slide <slide_id> <presentation_id> "título"
core/run tools/slides/gslides preview --account personal <presentation_id>   # download slide PNGs for visual inspection
core/run tools/slides/gslides apply --account personal <presentation_id> requests.json
core/run tools/slides/gslides export <url_or_id> --format pdf                # public export fallback without OAuth
core/run tools/slides/gslides sample <url_id_or_pdf> --out dir --max-samples 25 # keyframe visual clustering
```

**`read` prints element ids on purpose** — they are exactly what a `batchUpdate` request needs, so
reading a deck hands back the handles for editing it, no second raw-JSON fetch.

**`sample` clusters progressive animations and outputs key slides** — inspect visual diagrams without
saturating model context.

**`apply` is the real boundary; the other write commands are conveniences over it.** The Slides API is
itself a list of typed requests, so the CLI wraps that list rather than inventing a DSL that would
go stale the moment Google adds a request type. `--json` on `read` gives the input side of the
same shape.

Two auth grants (same split as [`../files/`](../files/CONTEXT.md)), the rendering facts the API
doesn't document, per-frame motion via `batchUpdate`, and why Slidev is gone: all in
[`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What the API actually returns, learned the expensive way — read alongside `CONTEXT.md`. |
| [`deck_sample.py`](deck_sample.py) | [`deck_sample.pyi`](deck_sample.pyi) | `parse_slide_target`, `download_public_export`, `extract_slide_texts`, `clean_slide_lines`, `cluster_and_sample` | deck_sample.py — Ingestion, progressive clustering and visual sampling for slide decks |
| [`gslides`](gslides) | — | — | Google Slides CLI: auth, list, read, new, add, text, apply, preview, export, sample |
| [`slides_core.py`](slides_core.py) | [`slides_core.pyi`](slides_core.pyi) | `get_service`, `get_presentation`, `list_presentations`, `create`, `apply` | slides_core.py — Google Slides read+write boundary (account-agnostic) for Core/tools/slides/gslides |
| [`slides_geom.py`](slides_geom.py) | [`slides_geom.pyi`](slides_geom.pyi) | `rotation_deg`, `eff_scale`, `compose_transforms`, `bounds` | slides_geom.py — Google Slides transform algebra: rotation, effective scale, composition, bounds |
| [`slides_outline.py`](slides_outline.py) | [`slides_outline.pyi`](slides_outline.pyi) | `element_text`, `kind`, `outline` | slides_outline.py — a deck as navigable text: slide index, element ids, and the words on them |
<!-- routing:end -->
