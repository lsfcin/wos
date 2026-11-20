# pdf
> T1 unit tests for the PDF twin. The PDFs are built in bytes and the engine is faked: no GPU, no network, no model.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_pdf_boundary.py`](test_pdf_boundary.py) | [`test_pdf_boundary.pyi`](test_pdf_boundary.pyi) | — | T0 one door: in core/, a PDF is opened raw only by pdf_meta.py (poppler) and pdf_engine.py (the engines). Every other file asks core/run tools/pdf/<leaf>. Zero-token, no network. |
| [`test_pdf_figures.py`](test_pdf_figures.py) | [`test_pdf_figures.pyi`](test_pdf_figures.pyi) | `crop` | T1 pdf figures: a logo repeated on every page is one decorative figure, distinct figures stay distinct, and the audit's word coverage counts what the twin kept. Zero-token, no network. |
| [`test_pdf_twin.py`](test_pdf_twin.py) | [`test_pdf_twin.pyi`](test_pdf_twin.pyi) | `make_pdf`, `fake_engine`, `said`, `build`, `offline` | T1 pdf twin: the frontmatter says what was converted and when it went stale, the git rule follows the origin, and a secret keeps the whole twin out of git. Zero-token, no network, no engine. |
<!-- routing:end -->
