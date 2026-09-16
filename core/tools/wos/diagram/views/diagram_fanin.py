# The wiring fan-in: how many features one switch point carries, and which points carry the load.
#
# The enforcement matrix draws this same relation as 69 x 25 cells and spends almost all of them on
# the 43 points that carry exactly one feature. Read as fan-in it is two sentences: mirror.sh
# switches fourteen skills, norms.py switches ten norms, and everything else is one-to-one. That is
# architecture the grid was hiding rather than showing.
#
# THREE SHAPES, ON PURPOSE AND TEMPORARILY. Lucas, 2026-08-18, asked to see all of them rendered
# before cutting, which is the front's own pacing — "we are still at the level of trying different
# visualizations to cut it later". When he picks one, the other two go and this file holds one
# drawing again, like every other file in this directory. See views/CONTEXT.md.
from html import escape

ROW = 16          # one feature per row inside a hub: fourteen lines converging LOOK like fourteen
HUB_GAP = 20
LABEL_W = 168     # the feature-name column, right-aligned into the convergence
LINK_W = 96
PAD = 12
BAR = 15          # same unit as the lifecycle bands, so the two drawings stay comparable
HUB_MIN = 2       # a point carrying one feature is not a fan-in; the tail says how many there are


def _split(points: list) -> tuple:
    """(hubs, tail) — the points worth drawing as nodes, and the count of one-to-one points.

    A one-to-one point is a real fact and a boring one: it is what a switch normally looks like.
    Drawing 43 of them is the wallpaper this view exists to replace, so they are COUNTED rather
    than dropped — a collapsed tail states the same total, and the reader can see nothing is hidden.
    """
    hubs = [(point, names) for point, names in points if len(names) >= HUB_MIN]
    return hubs, len(points) - len(hubs)


def _curve(y_from: float, y_to: float) -> str:
    x0, x1 = LABEL_W, LABEL_W + LINK_W
    return (f'<path class="link" d="M{x0} {y_from:.1f} C{x0 + LINK_W * 0.45:.1f} {y_from:.1f} '
            f'{x1 - LINK_W * 0.45:.1f} {y_to:.1f} {x1} {y_to:.1f}" />')


def _hub(point: str, names: list, top: float) -> tuple:
    """One hub: its features on the left, converging into the file that switches them all off."""
    height = ROW * len(names)
    centre = top + height / 2
    out = [_curve(top + ROW * i + ROW / 2, centre) for i in range(len(names))]
    out += [f'<text class="feat" x="{LABEL_W - 8}" y="{top + ROW * i + ROW / 2 + 4:.1f}">'
            f'{escape(name)}</text>' for i, name in enumerate(names)]
    out.append(f'<g class="hub"><title>{escape(point)}</title>'
               f'<circle cx="{LABEL_W + LINK_W}" cy="{centre:.1f}" r="{3 + len(names) ** 0.5:.1f}"/>'
               f'<text class="hub" x="{LABEL_W + LINK_W + 12}" y="{centre + 4:.1f}">'
               f'{escape(point)} <tspan class="cnt">{len(names)}</tspan></text></g>')
    return '\n'.join(out), height


def render_graph(points: list, dangling: list) -> str:
    """SHAPE 1 — converging node-link. Every feature is a line, so the load is a visual mass.

    Node count stays inside what node-link drawings are good for: four hubs, one collapsed tail and
    one loose end, against Ghoniem's ~20-node ceiling (core/refs/REFS.md § Tooling).
    The 107-node routing spine is far past it, which is why that one reads as wallpaper and this
    one does not.
    """
    hubs, tail = _split(points)
    body, y = [], float(PAD)
    for point, names in hubs:
        drawn, height = _hub(point, names, y)
        body.append(drawn)
        y += height + HUB_GAP
    for text, klass in ((f'{tail} further points, one feature each', 'tail'),
                        (f'{len(dangling)} feature switched by nothing at all: '
                         f'{escape(", ".join(dangling))}', 'loose') if dangling else ('', '')):
        if not text:
            continue
        body.append(f'<text class="{klass}" x="{PAD}" y="{y + 11:.1f}">{text}</text>')
        y += ROW + 8
    width = LABEL_W + LINK_W + max((len(p) for p, _s in hubs), default=30) * 7 + 60
    return (f'<svg class="fanin" viewBox="0 0 {width} {y + PAD:.0f}" width="{width}" '
            f'height="{y + PAD:.0f}" role="img" aria-label="wiring fan-in">'
            f'{"".join(body)}</svg>')


def render_bars(points: list, dangling: list, grain: str) -> str:
    """SHAPE 2 and 3 — position and length, the strongest channels (views/CONTEXT.md).

    One renderer, called twice: `grain` only names what a point IS. The file grain says which file
    to edit; the directory grain matches the matrix's own columns, and the two disagree wherever a
    feature spans layers — `latex` is one row and two files in two directories.
    """
    hubs, tail = _split(points)
    rows = [_bar(point, len(names), ', '.join(names)) for point, names in hubs]
    rows.append(_bar(f'{tail} further {grain}s', 1, 'one feature each', klass='bar tail'))
    for name in dangling:
        rows.append(_bar(name, 0, 'no switch point at all', klass='bar loose'))
    return f'<div class="fbars">{"".join(rows)}</div>'


def _bar(label: str, n: int, title: str, klass: str = 'bar') -> str:
    return (f'<div class="{klass}"><span class="pt">{escape(label)}</span>'
            f'<span class="run" style="width:{max(n * BAR, 2)}px" title="{escape(title)}"></span>'
            f'<span class="n">{n or "✗"}</span></div>')


def legend() -> str:
    return ('<p class="note">A point is a file that calls <code>feature_law.is_enabled()</code>, '
            'read from <code>core/features.txt</code> § wired — so a wrong edge here is a wrong '
            'registry row. <b>Two points carry a third of the workspace</b>: switching off '
            '<code>mirror.sh</code> takes fourteen skills with it and <code>norms.py</code> ten '
            'norms, which is deliberate — a group with one publisher is switchable at all, and the '
            'alternative was fourteen call sites. It is still the concentration to know about '
            'before the ablation runs, because those two rows can never be ablated apart.</p>')
