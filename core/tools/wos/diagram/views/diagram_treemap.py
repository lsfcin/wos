# Folder mass: how much of the workspace each directory actually is, by tracked bytes.
#
# The question it answers is the one a routing table cannot: the spine says core/ holds hooks and
# tools, and only area says that those two are most of the workspace while a directory beside them
# is a rounding error. Squarified rather than sliced, so a small directory stays a readable
# rectangle instead of a sliver.
from html import escape

WIDTH, HEIGHT = 960, 520
MIN_LABEL = 34          # below this a rectangle gets a tooltip instead of a label it cannot fit


def _worst(row: list, length: float) -> float:
    """The worst aspect ratio a row would produce — the quantity squarification minimises
    (Bruls, Huizing & van Wijk). Areas arrive already scaled to pixel units."""
    total = sum(row)
    if total <= 0 or length <= 0 or min(row) <= 0:
        return float('inf')
    return max(length ** 2 * max(row) / total ** 2, total ** 2 / (length ** 2 * min(row)))


def _layout(values: list, x: float, y: float, w: float, h: float) -> list:
    """Squarified treemap rectangles, in the order the values arrive (sorted descending).

    Values are normalised to pixel area once, up front: each row then consumes exactly the strip
    it is thick, so the remaining rectangle stays consistent without re-scaling.
    """
    total = sum(values)
    if total <= 0:
        return []
    scaled = [value * (w * h) / total for value in values]
    rects: list = []
    i = 0
    while i < len(scaled):
        length = min(w, h)
        row, best = [], float('inf')
        j = i
        while j < len(scaled):
            ratio = _worst(row + [scaled[j]], length)
            if row and ratio > best:
                break
            row, best = row + [scaled[j]], ratio
            j += 1
        thickness = sum(row) / length if length else 0
        offset = 0.0
        for value in row:
            side = value / thickness if thickness else 0
            if w >= h:
                rects.append((x, y + offset, thickness, side))
            else:
                rects.append((x + offset, y, side, thickness))
            offset += side
        if w >= h:
            x, w = x + thickness, w - thickness
        else:
            y, h = y + thickness, h - thickness
        i = j
    return rects


def _palette_index(name: str, families: list) -> int:
    """Colour by top-level directory, indexed off a sorted list rather than a hash: a hash is
    randomised per process, and a picture that changes colour between two identical runs cannot
    be compared with --check."""
    family = name.split('/')[0]
    return families.index(family) % 8 if family in families else 0


def _fit(name: str, width: float) -> str:
    """Clip a label to its own rectangle. A name spilling past its cell reads as belonging to the
    neighbour, which is worse than the ellipsis — and the full name is in the tooltip either way."""
    room = int((width - 12) / 6.6)
    return name if len(name) <= room else name[:max(room - 1, 1)] + '…'


def render(rows: list) -> str:
    rows = [r for r in rows if r[2] > 0]
    if not rows:
        return '<p class="note">no tracked files found</p>'
    families = sorted({name.split('/')[0] for name, _files, _size in rows})
    rects = _layout([size for _n, _f, size in rows], 0, 0, WIDTH, HEIGHT)
    total = sum(size for _n, _f, size in rows)

    out = [f'<svg class="treemap" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" '
           f'preserveAspectRatio="xMidYMid meet" role="img" aria-label="folder mass">']
    for (name, files, size), (x, y, w, h) in zip(rows, rects):
        share = size / total
        title = (f'{name} — {files} tracked files, {size // 1024} KB, '
                 f'{share:.1%} of tracked mass')
        out.append(f'<g class="cell c{_palette_index(name, families)}"><title>{escape(title)}'
                   f'</title><rect x="{x:.1f}" y="{y:.1f}" width="{max(w - 1, 0):.1f}" '
                   f'height="{max(h - 1, 0):.1f}" />')
        if w > MIN_LABEL * 2 and h > MIN_LABEL:
            out.append(f'<text x="{x + 6:.1f}" y="{y + 17:.1f}">{escape(_fit(name, w))}</text>'
                       f'<text class="sub" x="{x + 6:.1f}" y="{y + 32:.1f}">{files} files</text>')
        out.append('</g>')
    out.append('</svg>')
    return '\n'.join(out)


def legend(rows: list) -> str:
    total = sum(size for _n, _f, size in rows)
    files = sum(count for _n, count, _s in rows)
    return (f'<p class="note">{files} tracked files, {total // 1024} KB, folded to two levels. '
            'The inventory is <code>git ls-files</code> and never a directory walk — which is what '
            'keeps <code>.venv</code>, <code>Downloads/</code> and the trash out of a picture of '
            'the workspace, three directories that would otherwise dwarf everything real.</p>')
