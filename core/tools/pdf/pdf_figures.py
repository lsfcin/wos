# pdf_figures.py — a twin's figures: the same image found twice is one figure, a logo on every page is decoration, each gets a name, a file and a markdown block.
#
# DEDUP BY LOOK, NOT BY BYTES. The engine crops each figure from a render, so the coat of arms on
# every page of a resolution comes back as N files whose bytes differ by a pixel. An average hash
# (16x16 grey, one bit per pixel against the mean) calls them one image, and it is described once.
from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pdf_meta

HASH_SIDE = 16
DECORATIVE_PAGES = 3   # the same image on this many pages is a letterhead, not content
PREVIEW_SIDE = 1024    # the versioned JPEG: small enough for git, big enough to read a chart
PREVIEW_QUALITY = 60
EMBEDDED_MIN_SIDE = 64


@dataclass
class Figure:
    name: str                     # p03-fig1: page, then order on that page
    page: int
    source: Path                  # the engine's crop
    look: str                     # the average hash
    same_as: str | None = None    # the first figure with this look
    decorative: bool = False
    pages: set = field(default_factory=set)


def look(image: Path) -> str:
    from PIL import Image
    grey = Image.open(image).convert('L').resize((HASH_SIDE, HASH_SIDE))
    pixels = list(grey.tobytes())
    mean = sum(pixels) / len(pixels)
    return ''.join('1' if p > mean else '0' for p in pixels)


def name_all(engine_figures: list[dict], total_pages: int) -> list[Figure]:
    """Name every figure pNN-figK, and point each repeat at its first appearance."""
    figures, first, per_page = [], {}, {}
    for entry in engine_figures:
        page = entry['page']
        per_page[page] = per_page.get(page, 0) + 1
        fig = Figure(f'p{page:02d}-fig{per_page[page]}', page, Path(entry['file']), look(Path(entry['file'])))
        if fig.look in first:
            fig.same_as = first[fig.look].name
            first[fig.look].pages.add(page)
        else:
            first[fig.look] = fig
            fig.pages.add(page)
        figures.append(fig)
    for fig in first.values():
        fig.decorative = len(fig.pages) >= min(DECORATIVE_PAGES, max(2, total_pages))
    for fig in figures:
        if fig.same_as:
            fig.decorative = next(f for f in first.values() if f.name == fig.same_as).decorative
    return figures


def embedded_count(pdf: Path) -> int:
    """Distinct images the PDF embeds — the free count the engine's figures are audited against."""
    with tempfile.TemporaryDirectory(prefix='pdf-img-') as tmp:
        from PIL import Image
        looks = set()
        for png in pdf_meta.images(pdf, Path(tmp) / 'i'):
            with Image.open(png) as im:
                if min(im.size) >= EMBEDDED_MIN_SIDE:
                    looks.add(look(png))
        return len(looks)


def save(fig: Figure, img_dir: Path, preview: bool) -> str:
    """Keep the original PNG; add the small JPEG when the git rule versions previews. Returns the
    file the markdown links to."""
    img_dir.mkdir(parents=True, exist_ok=True)
    png = img_dir / f'{fig.name}.png'
    shutil.copyfile(fig.source, png)
    if not preview:
        return f'img/{png.name}'
    from PIL import Image
    im = Image.open(png).convert('RGB')
    im.thumbnail((PREVIEW_SIDE, PREVIEW_SIDE))
    im.save(img_dir / f'{fig.name}.jpg', quality=PREVIEW_QUALITY, optimize=True)
    return f'img/{fig.name}.jpg'


def block(fig: Figure, link: str, description=None, ocr_text: str = '') -> str:
    """One figure in the twin: the image, who described it, the description, the OCR verbatim."""
    if fig.same_as:
        return f'![{fig.name}]({link})\n\n<!-- figure {fig.name} | same image as {fig.same_as} -->\n'
    tags = [f'figure {fig.name}', f'described_by: {description.by}',
            f'ocr_overlap: {description.overlap}', f'needs_review: {str(description.needs_review).lower()}']
    if fig.decorative:
        tags.append('decorative: true')
    text = f'![{fig.name}]({link})\n\n<!-- {" | ".join(tags)} -->\n{description.text or "[no description]"}\n'
    if ocr_text:
        text += f'\n~~~text ocr\n{ocr_text}\n~~~\n'
    return text
