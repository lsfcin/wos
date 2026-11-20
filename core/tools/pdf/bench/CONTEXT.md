# bench
> The two bake-offs behind the PDF twin, re-runnable: which engine converts, and which describer reads figures. Results live in core/experiments/.

Both scripts measure the production path — the engine worker and the describer backends the leaves use — so a number here is a number about the tool. Neither ships a corpus: the PDFs, the figure images and the answer keys are real and some are private, so they are passed in as a folder and never versioned.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`describers.py`](describers.py) | [`describers.pyi`](describers.pyi) | `hits`, `run`, `main` | Usage: core/run tools/pdf/bench/describers.py <set-dir> [--describers agy,claude,local] — describe every image in a set with each describer ALONE (no chain), then score facts hit against <set-dir>/keys.json and the OCR cross-check; one TSV row per image×describer and a total |
| [`engines.py`](engines.py) | [`engines.pyi`](engines.pyi) | `measure`, `main` | Usage: core/run tools/pdf/bench/engines.py <corpus-dir> [--engines docling,pymupdf] — convert every PDF in a folder with each engine through the production worker; one TSV row per PDF×engine: coverage, figures, tables, seconds, peak VRAM |
<!-- routing:end -->
