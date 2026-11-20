# pdf_engine.py — the conversion worker: one PDF in, markdown per page plus every figure out. Runs under .venv-pdf, never .venv.
#
# WHY A WORKER. docling pulls torch and ~120 packages; the workspace venv every hook starts on stays
# light. pdf_twin.py (under .venv) spawns this file with .venv-pdf's python and reads one JSON file.
# So this file imports nothing from the workspace: only the engines and the stdlib.
#
# Contract: `python pdf_engine.py <docling|pymupdf> <pdf> <figure-dir>` writes <figure-dir>/RESULT:
#   {"engine": "<name> <version>", "pages": ["<md of page 1>", ...],
#    "figures": [{"page": 3, "file": "<figure-dir>/f0007.png"}, ...]}
# Each figure's place in its page's markdown is the line FIGURE, in the same order as `figures`.
# A file and not stdout: both engines print progress there (RapidOCR, the layout parser).
from __future__ import annotations

import importlib.metadata
import json
import re
import sys
from pathlib import Path

FIGURE = '<!-- figure -->'
RESULT = 'engine.json'
MIN_SIDE = 32   # smaller crops are rules, bullets and specks, not figures


def _docling(pdf: Path, out: Path) -> tuple[list[str], list[dict]]:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.generate_picture_images = True
    opts.images_scale = 2.0
    doc = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
                            ).convert(str(pdf)).document
    count = max(doc.pages) if doc.pages else 0
    figures: list[dict] = []
    by_page: dict[int, list[dict]] = {}
    for item, _level in doc.iterate_items():
        if type(item).__name__ != 'PictureItem' or not item.prov:
            continue
        image = item.get_image(doc)
        page = item.prov[0].page_no
        entry = {'page': page, 'file': str(out / f'f{len(figures):04d}.png')}
        if image is None or min(image.size) < MIN_SIDE:
            entry['file'] = None
        else:
            image.save(entry['file'])
        figures.append(entry)
        by_page.setdefault(page, []).append(entry)
    pages = [doc.export_to_markdown(page_no=n, image_placeholder=FIGURE) for n in range(1, count + 1)]
    for n, md in enumerate(pages, 1):   # a crop too small to be a figure loses its own placeholder
        entries, parts = by_page.get(n, []), md.split(FIGURE)
        pages[n - 1] = parts[0] + ''.join(
            (FIGURE if i < len(entries) and entries[i]['file'] else '') + part
            for i, part in enumerate(parts[1:]))
    return pages, [f for f in figures if f['file']]


IMAGE_LINK = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')


def _pymupdf(pdf: Path, out: Path) -> tuple[list[str], list[dict]]:
    import pymupdf4llm

    chunks = pymupdf4llm.to_markdown(str(pdf), page_chunks=True, write_images=True,
                                     image_path=str(out), image_format='png')
    pages, figures = [], []
    for n, chunk in enumerate(chunks, 1):
        def keep(match: re.Match, page: int = n) -> str:
            figures.append({'page': page, 'file': str(Path(match.group(1)).resolve())})
            return FIGURE
        pages.append(IMAGE_LINK.sub(keep, chunk['text']))
    return pages, figures


ENGINES = {'docling': (_docling, 'docling'), 'pymupdf': (_pymupdf, 'pymupdf4llm')}


def main() -> int:
    engine, pdf, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    convert, package = ENGINES[engine]
    pages, figures = convert(pdf, out)
    (out / RESULT).write_text(json.dumps({'engine': f'{package} {importlib.metadata.version(package)}',
                                          'pages': pages, 'figures': figures}, ensure_ascii=False),
                              encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
