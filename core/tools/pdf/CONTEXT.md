# pdf
> A PDF becomes its twin: a sibling folder whose .md holds all the text, every figure described, and the hash that says when it went stale. Provider leaves: `docling`, `pymupdf`.

```
core/run tools/pdf/docling <pdf>... [--from <file>] [--describer agy|local|claude] [--origin <url>] [--description <text>] [--force]
core/run tools/pdf/docling <pdf> --review          # render the flagged pages for an agent to compare
core/run tools/pdf/docling <pdf> --reviewed-by <who>
```

`docling` (GPU, reads Portuguese scans and tables) is the default; `pymupdf` is the CPU path, seconds to a minute per PDF, with fewer tables. `res.pdf` gets `res/res.md`: frontmatter with the hash that marks it stale, `<!-- page N -->` anchors, and one block per figure — described by [`../describe.py`](../describe.py), checked against the figure's own OCR. Why these engines and describers: [`pdf-engine.md`](../../experiments/pdf-engine.md), [`vlm-describe.md`](../../experiments/vlm-describe.md).

The `.md` is versioned; the PNG originals are gitignored; JPEG previews are versioned unless `--origin` names a live URL. A secret in the text gitignores the whole twin. The engines run in their own venv, `.venv-pdf`, through [`pdf_engine.py`](pdf_engine.py).

**One door.** A PDF is opened raw only by [`pdf_meta.py`](pdf_meta.py) (poppler) and `pdf_engine.py` (the engines); `test_pdf_boundary.py` refuses the rest of `core/`. Another family asks `core/run tools/pdf/poppler text|render`, as slides does. An agent reads the twin: [`pdf-gate.py`](../../hooks/read/pdf-gate.py) refuses a Read or a raw shell reader of a PDF until it has.

## Install
> feature: pdf

- **Precondition:** `core/run tools/wos/deps --feature pdf`
- **Install:** `uv venv -p 3.12 .venv-pdf && uv pip install --python .venv-pdf/bin/python -r core/tools/pdf/requirements-pdf.txt` (Windows: `.venv-pdf\Scripts\python.exe`), then `sudo apt-get install -y tesseract-ocr-por poppler-utils`
- **Verify:** the precondition passes

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`bench/`](bench/CONTEXT.md) | The two bake-offs behind the PDF twin, re-runnable: which engine converts, and which describer reads figures. Results live in core/experiments/. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`docling`](docling) | — | — | a PDF becomes its twin folder (full .md, figures described, metadata) through Docling: GPU, scans in Portuguese, tables |
| [`pdf_cli.py`](pdf_cli.py) | [`pdf_cli.pyi`](pdf_cli.pyi) | `parse`, `label`, `flagged_pages`, `review`, `stamp` | pdf_cli.py — the command line both engine leaves share: many PDFs per call, one line each, a summary naming the failures, and the review pass. |
| [`pdf_engine.py`](pdf_engine.py) | [`pdf_engine.pyi`](pdf_engine.pyi) | `main` | pdf_engine.py — the conversion worker: one PDF in, markdown per page plus every figure out. Runs under .venv-pdf, never .venv. |
| [`pdf_figures.py`](pdf_figures.py) | [`pdf_figures.pyi`](pdf_figures.pyi) | `Figure`, `look`, `name_all`, `embedded_count`, `save` | pdf_figures.py — a twin's figures: the same image found twice is one figure, a logo on every page is decoration, each gets a name, a file and a markdown block. |
| [`pdf_meta.py`](pdf_meta.py) | [`pdf_meta.pyi`](pdf_meta.pyi) | `sha256`, `twin_of`, `source_of`, `is_twin`, `twin_state` | pdf_meta.py — the one place a PDF is opened raw, and what a twin says about it: hash, pdfinfo, text layer, pages rendered, the free audit, the frontmatter, and whether the twin is still true. |
| [`pdf_twin.py`](pdf_twin.py) | [`pdf_twin.pyi`](pdf_twin.pyi) | `EngineMissing`, `run_engine`, `origin_live`, `build` | pdf_twin.py — one PDF becomes its twin: a sibling folder whose .md holds all the text, every figure described, and the metadata that says whether the twin is still true. |
| [`poppler`](poppler) | — | — | a PDF's raw pages for another tool: the text layer split by form feed, or each page as a PNG. An agent reads the twin instead. |
| [`pymupdf`](pymupdf) | — | — | a PDF becomes its twin folder through PyMuPDF4LLM: CPU, seconds to a minute per PDF, finds fewer tables than docling |
| [`requirements-pdf.txt`](requirements-pdf.txt) | — | — | The conversion engines for core/tools/pdf, installed into .venv-pdf and never into .venv: docling pulls torch and ~120 packages, and the workspace venv stays light for every hook that starts on it. Versions are the ones the 2026-09-25 bake-off measured (core/experiments/pdf-engine.md). Install: core/tools/pdf/CONTEXT.md § Install. |
<!-- routing:end -->
