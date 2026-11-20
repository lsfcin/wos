# pdf_meta.py — the one place a PDF is opened raw, and what a twin says about it: hash, pdfinfo, text layer, pages rendered, the free audit, the frontmatter, and whether the twin is still true.
#
# Everything here is poppler + tesseract + stdlib: zero tokens, no GPU. Every other file reaches a
# PDF through this module or through `core/run tools/pdf/<leaf>` — RAW_COMMANDS and RAW_MODULES are
# what test_pdf_boundary.py refuses anywhere else, and what core/hooks/read/pdf-gate.py refuses an
# agent before it has read the twin. The frontmatter values are
# written as JSON, which is valid YAML, so one writer needs no YAML library and the reader
# (`read_frontmatter`) gets back exactly what was written.
from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

PDFINFO = {'Title': 'title', 'Author': 'author', 'Subject': 'subject', 'Keywords': 'keywords',
           'Creator': 'creator', 'Producer': 'producer', 'CreationDate': 'created',
           'ModDate': 'modified', 'Pages': 'pages', 'Encrypted': 'encrypted'}
TEXT_PAGE = 10     # a page with fewer pdftotext words than this has no usable text layer
WORD = re.compile(r'[a-zà-ÿ0-9]{3,}')
# The raw readers: a PDF opened by any of these skips its twin. Commands are what a subprocess or a
# shell spawns; modules are what Python imports. The engine modules belong to pdf_engine.py alone.
RAW_COMMANDS = ('pdftotext', 'pdftoppm', 'pdfimages', 'pdfinfo', 'pdftohtml', 'pdftocairo', 'mutool')
RAW_MODULES = ('fitz', 'pymupdf', 'pymupdf4llm', 'pypdf', 'PyPDF2', 'pdfplumber', 'pdfminer',
               'docling', 'markitdown')
# `description` is the one field a person writes (pdf_cli `--description`): what the routing table
# shows for the twin. The engine cannot know what a PDF is for, so a rebuild keeps it.
FIELDS = ('description', 'source', 'sha256', 'origin', 'origin_checked', 'pdf', 'text_layer', 'engine',
          'audit', 'needs_review', 'reviewed_by')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def twin_of(pdf: Path) -> Path:
    return pdf.with_suffix('') / f'{pdf.stem}.md'


def source_of(twin: Path) -> Path | None:
    """The PDF a `<stem>/<stem>.md` is the twin of, or None when that file is no twin."""
    if twin.suffix != '.md' or twin.parent.name != twin.stem:
        return None
    return next((pdf for suffix in ('.pdf', '.PDF') if (pdf := twin.parent.with_name(twin.stem + suffix)).is_file()),
                None)


def is_twin(path: Path) -> bool:
    """Did this tool write `path`? Asked of the twin's own stamp — `<stem>/<stem>.md` whose frontmatter
    names `../<stem>.pdf` as its source — never of the PDF beside it: branches/casinhas keeps its PDFs
    in the Drive, and its twins in git. core/hooks/file_law.py asks this to exempt a twin from the
    authoring caps, which a 19-page regimento cannot meet and was never written to."""
    if path.suffix != '.md' or path.parent.name != path.stem:
        return False
    try:
        return str(read_frontmatter(path).get('source', '')).lower() == f'../{path.stem}.pdf'.lower()
    except (OSError, ValueError, yaml.YAMLError):
        return False


def twin_state(pdf: Path) -> tuple[str, Path]:
    """The twin beside `pdf` and which of three states it is in — the one definition the build and
    the read gate both ask (the PDF's own mirror of core/hooks/read/chain.py:interface_state).

    `absent` — no twin, or one with no hash to compare. `stale` — the PDF changed after its twin
    was written. `fresh` — the twin still says what the PDF says.
    """
    twin = twin_of(pdf)
    recorded = read_frontmatter(twin).get('sha256')
    if not recorded:
        return 'absent', twin
    return ('fresh' if recorded == sha256(pdf) else 'stale'), twin


def pdfinfo(path: Path) -> dict:
    out = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, encoding='utf-8').stdout
    info = {}
    for line in out.splitlines():
        key, _, value = line.partition(':')
        if key in PDFINFO and value.strip():
            info[PDFINFO[key]] = value.strip()
    info['pages'] = int(info.get('pages', 0))
    info['encrypted'] = info.get('encrypted', 'no').startswith('yes')
    return info


def page_texts(path: Path) -> list[str]:
    """pdftotext, one string per page (form feed is poppler's page separator)."""
    out = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True, text=True,
                         encoding='utf-8').stdout
    return out.split('\f')[:-1] if out.endswith('\f') else out.split('\f')


def text_layer(pages: list[str]) -> str:
    with_text = sum(len(p.split()) >= TEXT_PAGE for p in pages)
    if with_text == len(pages):
        return 'born-digital'
    return 'scanned' if with_text == 0 else 'mixed'


def render(path: Path, prefix: Path, pages: list[int] | None = None, dpi: int = 150) -> list[Path]:
    """Each page as `<prefix>-<n>.png` (poppler pads n to the page count's width), in page order.
    A page poppler cannot render is simply missing from the list; the caller decides if that fails."""
    for n in pages or [None]:
        span = ['-f', str(n), '-l', str(n)] if n else []
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', *span, str(path), str(prefix)], capture_output=True)
    return sorted(prefix.parent.glob(f'{prefix.name}-*.png'), key=lambda p: int(p.stem.rsplit('-', 1)[1]))


def images(path: Path, prefix: Path) -> list[Path]:
    """Every image the PDF embeds, as `<prefix>-NNN.png`."""
    subprocess.run(['pdfimages', '-png', str(path), str(prefix)], capture_output=True)
    return sorted(prefix.parent.glob(f'{prefix.name}-*.png'))


def ocr_page(path: Path, page: int) -> str:
    with tempfile.TemporaryDirectory(prefix='pdf-ocr-') as tmp:
        return '\n'.join(subprocess.run(['tesseract', str(img), '-', '-l', 'por+eng'],
                                        capture_output=True, text=True, encoding='utf-8').stdout
                         for img in render(path, Path(tmp) / 'p', [page], 200))


def reference(path: Path, pages: list[str]) -> str:
    """What the PDF says, from the free tools: the text layer, and OCR where a page has none."""
    return '\n'.join(text if len(text.split()) >= TEXT_PAGE else ocr_page(path, n)
                     for n, text in enumerate(pages, 1))


def coverage(reference_text: str, markdown: str) -> float:
    """Share of the reference's words (with multiplicity) that the twin kept."""
    ref = collections.Counter(WORD.findall(reference_text.lower()))
    got = collections.Counter(WORD.findall(markdown.lower()))
    return round(sum(min(c, got[w]) for w, c in ref.items()) / max(1, sum(ref.values())), 2)


def counts(markdown: str) -> dict:
    return {'tables': len(re.findall(r'^\|.*\|\s*\n\|[\s:|-]+\|', markdown, re.M)),
            'formulas': len(re.findall(r'\$\$.+?\$\$|<!-- formula', markdown, re.S))}


def render_frontmatter(fields: dict) -> str:
    return '---\n' + ''.join(f'{k}: {json.dumps(fields.get(k), ensure_ascii=False)}\n'
                             for k in FIELDS) + '---\n'


def read_frontmatter(twin: Path) -> dict:
    """The frontmatter of an existing twin, or {} when there is none to read."""
    if not twin.exists():
        return {}
    text = twin.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        return {}
    return yaml.safe_load(text[4:text.index('\n---\n', 4)]) or {}


def replace_frontmatter(twin: Path, **changes) -> None:
    text = twin.read_text(encoding='utf-8')
    body = text[text.index('\n---\n', 4) + 5:]
    twin.write_text(render_frontmatter({**read_frontmatter(twin), **changes}) + body, encoding='utf-8', newline='\n')
