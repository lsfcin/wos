# The summary layer: the two questions answered before any detail arrives.
#
# Lucas, on the first version of the page: "I am not confident it helps me to understand... it is
# not visually informative yet." The diagnosis was never the data — it was that the page OPENS on
# maximum detail, so both of his reads are hunts. This module draws what he asked for instead:
# (1) is the workspace well tied, where is it loose, what is noise; (2) what is missing.
#
# Three encodings were built and shown at real scale; Lucas picked the heat grid on 2026-08-18 and
# the other two are gone rather than kept as options. What it won on is compression: the whole
# workspace is 30 cells, so the shape arrives before any reading does, and a layer that was declared
# and never built is a row of dots nobody has to hunt for.
#
# It wins that DESPITE the encoding hierarchy rather than because of it — colour and density are
# the weakest channels for judging quantity (Cleveland & McGill, core/refs/REFS.md § Tooling),
# which is why every cell also carries its number. Density gets the eye to the region;
# the numeral answers once it is there.
from html import escape

# Hardest first. The order is the reading: a bar that starts red is a wall, one that is all grey is
# advice, and the difference lands before a label is read. Same order and same meaning as MARKS in
# diagram_matrix, because two orders for one idea is the asymmetry this workspace exists to catch.
STRENGTHS = ('blocks', 'warns', 'generates', 'advises', 'none')

STYLE = """
.ov { margin:0 0 26px; }
.ov h2 { margin:0 0 4px; }
.ov .q { color:var(--dim); font-size:12.5px; margin:0 0 12px; }
.finds { list-style:none; margin:0; padding:0; }
.finds li { display:grid; grid-template-columns:82px 1fr; gap:11px; padding:5px 0;
  border-top:1px solid var(--line); font-size:13px; }
.finds li:first-child { border-top:none; }
.finds .cnt { text-align:right; font-variant-numeric:tabular-nums; font-weight:600; }
.finds .of { color:var(--dim); font-weight:400; font-size:11.5px; }
.finds .zero .cnt, .finds .zero .txt { color:var(--dim); opacity:.65; font-weight:400; }
.finds .txt small { color:var(--dim); display:block; font-size:11px; margin-top:1px; }
table.heat { border-collapse:collapse; font-size:12px; font-variant-numeric:tabular-nums; }
table.heat th { color:var(--dim); font-weight:500; padding:4px 9px; }
table.heat th.l { text-align:right; }
table.heat td { border:1px solid var(--line); padding:5px 11px; text-align:center; min-width:52px; }
table.heat td.z { color:var(--dim); opacity:.4; }
.pair { display:flex; gap:34px; flex-wrap:wrap; align-items:flex-start; }
.pair h3 { font-size:12.5px; margin:0 0 2px; font-weight:600; }
.pair .q { margin:0 0 8px; }
"""


def _findings(items: list) -> str:
    """The gaps, as sentences with a magnitude and a target — never as absences to be spotted.

    A count with no denominator is a number; `28 of 68` is a proportion a reader can judge without
    knowing this workspace. A finding at zero stays on the list, dimmed: a list that hides its
    clean rows cannot be read as coverage.

    THE TARGET IS WHAT MAKES THE COUNT JUDGEABLE, and a row whose target nobody has decided says so
    out loud. Printing nothing there would let an undecided target pass for a met one, which is the
    same silence the whole list exists to break.
    """
    out = ['<ul class="finds">']
    for f in items:
        of = f'<span class="of"> of {f["of"]}</span>' if f['of'] is not None else ''
        met = f['target'] is not None and f['count'] == f['target']
        target = ('undecided' if f['target'] is None else
                  f'target {f["target"]}' + (' · met' if met else ''))
        out.append(f'<li class="{"zero" if met else ""}">'
                   f'<span class="cnt">{f["count"]}{of}</span>'
                   f'<span class="txt">{escape(f["text"])}'
                   f'<small>{escape(f["where"])} · <b>{target}</b></small></span></li>')
    return '\n'.join(out + ['</ul>'])


def _peak(*grids: list) -> int:
    """The busiest cell across EVERY grid drawn, so two grids side by side stay comparable.

    Scaling each one to its own maximum would draw the fifteen skills that enforce nothing as dark
    as the sixteen hooks that block a commit, and the whole point of putting them side by side is
    that those are not the same size of fact.
    """
    return max((max(s.values(), default=0) for g in grids for _l, s, _t in g), default=1) or 1


def _grid(layers: list, peak: int) -> str:
    """One declared layer per row, one enforcement strength per column.

    Density is per cell against `peak` rather than per row. A per-row scale would make every layer
    look equally enforced — `norms` is ten out of ten `advises` and would render as solid as the
    sixteen commit-blocking hooks, which is the opposite of the truth.
    """
    head = ''.join(f'<th>{escape(k)}</th>' for k in STRENGTHS)
    body = []
    for layer, strength, total in layers:
        cells = ''.join(
            f'<td class="{"z" if not strength.get(k) else ""}" '
            f'style="background:rgba(192,57,43,{strength.get(k, 0) / peak * 0.72:.3f})" '
            f'title="{strength.get(k, 0)} {escape(layer)} {escape(k)}">'
            f'{strength.get(k, 0) or "·"}</td>' for k in STRENGTHS)
        body.append(f'<tr><th class="l">{escape(layer)}</th>{cells}'
                    f'<th class="l">{total or "·"}</th></tr>')
    return f'<table class="heat"><tr><th></th>{head}<th></th></tr>{"".join(body)}</table>'


def render(automatic: list, on_demand: list, items: list) -> str:
    """The summary layer: how the workspace is tied, then what is loose or missing.

    TWO grids rather than one, split by what starts a feature. Merged, the workspace reads as
    though a third of it enforces nothing and is therefore dead weight — which is exactly the
    misreading that produced this split. Apart, the left grid is the whole enforcement story and
    the right one is a capability layer that was never supposed to push on anybody.
    """
    peak = _peak(automatic, on_demand)
    auto_n = sum(total for _l, _s, total in automatic)
    called_n = sum(total for _l, _s, total in on_demand)
    return (f'<section class="ov"><h2>how it is tied</h2>'
            f'<p class="q">declared layer against how hard each feature pushes, split by what '
            f'starts it. Darkness is how many, on one scale across both grids; a row of dots is a '
            f'layer that was declared and never built.</p>'
            f'<div class="pair">'
            f'<div><h3>automatic · {auto_n}</h3>'
            f'<p class="q">fires without being asked, so it has a moment</p>'
            f'{_grid(automatic, peak)}</div>'
            f'<div><h3>on-demand · {called_n}</h3>'
            f'<p class="q">waits to be called, so it has none</p>'
            f'{_grid(on_demand, peak)}</div></div>'
            f'<p class="note">The two are independent, which is why they are two columns in '
            f'<code>core/features.txt</code> and not one: eleven features cross. Six fire by '
            f'themselves and push on nobody — they compress, record, wipe, count. Five you invoke '
            f'by hand and they still push.</p></section>'
            f'<section class="ov"><h2>what is loose or missing</h2>'
            f'<p class="q">derived from the same declarations, so every row is a fact about the '
            f'workspace rather than a judgement about it</p>{_findings(items)}</section>')
