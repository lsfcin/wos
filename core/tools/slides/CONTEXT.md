# slides
> Presentations, read and edited in place. Provider leaf: `gslides` (Google Slides API); `pptx` builds the masters and layouts the API cannot.

```bash
core/run tools/slides/gslides list  --account personal --name "AI4Good"
core/run tools/slides/gslides read  --account personal <presentation_id>     # deck as navigable text
core/run tools/slides/gslides stats --account personal <presentation_id>     # style in numbers + archetype of each slide
core/run tools/slides/gslides lint  --account personal <presentation_id>     # small text, off the slide, over the template, off the footer line
core/run tools/slides/gslides new   --account personal "Aula 3"
core/run tools/slides/gslides text  --account personal --slide <slide_id> <presentation_id> "título"
core/run tools/slides/gslides preview --account personal --sheet <presentation_id>   # slide PNGs + 20-per-image contact sheets
core/run tools/slides/gslides apply --account personal <presentation_id> requests.json
core/run tools/slides/gslides export <url_or_id> --format pdf                # public export fallback without OAuth
core/run tools/slides/gslides sample <url_id_or_pdf> --out dir --max-samples 25 # keyframe visual clustering
core/run tools/slides/pptx template spec.json --out t.pptx                     # one master per section colour, same layouts in each
core/run tools/slides/pptx lint deck.pptx --fonts "Atkinson Hyperlegible Next" Anton   # Morph pairs, effect timing, the 1/3 rule, text size
core/run tools/slides/pptx flatten deck.pptx --out flat.pptx                   # one slide per click: the PDF reads as a flipbook
core/run tools/files/gdrive put --account personal --slides --name "template" t.pptx   # ...converted into Google Slides
```

**`read` prints element ids on purpose** — they are exactly what a `batchUpdate` request needs, so reading a deck hands back the handles for editing it, no second raw-JSON fetch.

**`sample` clusters progressive animations and outputs key slides** — inspect visual diagrams without saturating model context.

**`apply` is the real boundary; the other write commands are conveniences over it.** The Slides API is itself a list of typed requests, so the CLI wraps that list rather than inventing a DSL that would go stale the moment Google adds a request type. `--json` on `read` gives the input side of the same shape.

Two auth grants (same split as [`../files/`](../files/CONTEXT.md)), the rendering facts the API doesn't document, per-frame motion via `batchUpdate`, and why Slidev is gone: all in [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What the API actually returns, learned the expensive way — read alongside `CONTEXT.md`. |
| [`deck_sample.py`](deck_sample.py) | [`deck_sample.pyi`](deck_sample.pyi) | `parse_slide_target`, `download_public_export`, `render_pages`, `extract_slide_texts`, `clean_slide_lines` | deck_sample.py — Ingestion, progressive clustering and visual sampling for slide decks |
| [`gslides`](gslides) | — | — | Google Slides CLI: auth, list, read, stats, lint, new, add, text, apply, preview, export, sample |
| [`pptx`](pptx) | — | — | a slide template as real masters and layouts; lint a deck's motion and text; flatten every click into a slide for the PDF |
| [`pptx_check.py`](pptx_check.py) | [`pptx_check.pyi`](pptx_check.pyi) | `budget`, `lint`, `flatten` | pptx_check.py — motion read back from a .pptx: lint what a room or a PDF would get wrong, and flatten every click into its own slide |
| [`pptx_layouts.py`](pptx_layouts.py) | [`pptx_layouts.pyi`](pptx_layouts.pyi) | `section`, `split`, `content`, `statement`, `number` | pptx_layouts.py — every layout kind the template generator knows, as geometry over the shape primitives |
| [`pptx_masters.py`](pptx_masters.py) | [`pptx_masters.pyi`](pptx_masters.pyi) | `build`, `summary` | pptx_masters.py — a .pptx with one master per section colour, each carrying the same layouts |
| [`pptx_motion.py`](pptx_motion.py) | [`pptx_motion.pyi`](pptx_motion.pyi) | `q`, `transition`, `morph_key`, `appear`, `fade_in` | pptx_motion.py — motion a .pptx carries and a PDF cannot: transitions, click-timed effects, slide links |
| [`pptx_shapes.py`](pptx_shapes.py) | [`pptx_shapes.pyi`](pptx_shapes.pyi) | `box`, `placeholder`, `text`, `layout` | pptx_shapes.py — the DrawingML a layout is made of: a filled box, a placeholder, a fixed line of text |
| [`pptx_theme.py`](pptx_theme.py) | [`pptx_theme.pyi`](pptx_theme.pyi) | `slots`, `rewrite` | pptx_theme.py — one theme per section: the stock theme with its colour slots and fonts rewritten |
| [`slides_core.py`](slides_core.py) | [`slides_core.pyi`](slides_core.pyi) | `get_service`, `get_presentation`, `list_presentations`, `create`, `apply` | slides_core.py — Google Slides read+write boundary (account-agnostic) for Core/tools/slides/gslides |
| [`slides_geom.py`](slides_geom.py) | [`slides_geom.pyi`](slides_geom.pyi) | `rotation_deg`, `eff_scale`, `compose_transforms`, `bounds` | slides_geom.py — Google Slides transform algebra: rotation, effective scale, composition, bounds |
| [`slides_outline.py`](slides_outline.py) | [`slides_outline.pyi`](slides_outline.pyi) | `element_text`, `kind`, `outline` | slides_outline.py — a deck as navigable text: slide index, element ids, and the words on them |
| [`slides_style.py`](slides_style.py) | [`slides_style.pyi`](slides_style.pyi) | `runs`, `archetype`, `stats`, `lint` | slides_style.py — a deck's style read back from its JSON: statistics, the archetype of each slide, and lint |
<!-- routing:end -->
