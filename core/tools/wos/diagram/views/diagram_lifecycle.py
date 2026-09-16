# The lifecycle sequence: which features fire at which moment of a session, in the order they run.
#
# Lucas asked for this one by name — "sequences of thing1 -> thing2 -> thing3, how things are
# connected or not". The three drawings beside it are inventories that say WHAT EXISTS; this is the
# only one that says WHEN, and a session read top to bottom is the shape a person actually lives.
#
# It could not be drawn honestly until 2026-08-18, when the firing moment stopped being guessed from
# directory convention (core/hooks/trigger/trigger_law.py). Half its bands would have been hatched, and the
# norms would have sat on the wrong one.
#
# ORDER AND LENGTH CARRY THE QUANTITIES, per views/CONTEXT.md: a band's bar is as long as the
# features on it, so the pre-commit wall is visibly the wall. The on-demand features hang beside
# the chain rather than on it — they have no moment, which is what the `runs` column bought and
# what a drawing that put them somewhere would throw away.
from html import escape

BAR = 15          # one feature per unit of bar length: position and length, the strongest channels
LABEL = 132       # room for the longest moment name at 12.5px
GAP = 3


def _bar(moment: str, features: list) -> str:
    """One band. An EMPTY band keeps its row and says so: a moment nothing fires at is a gap in the
    chain, and it is only visible because the vocabulary is declared rather than collected from
    what happened to exist."""
    width = max(len(features) * BAR, 2)
    names = ', '.join(f['name'] for f in features)
    klass = 'band empty' if not features else 'band'
    return (f'<div class="{klass}"><span class="mom">{escape(moment)}</span>'
            f'<span class="run" style="width:{width}px" title="{escape(names)}"></span>'
            f'<span class="n">{len(features) or "—"}</span>'
            f'<span class="who">{escape(names) or "nothing fires here"}</span></div>')


def render(bands: list, on_demand: list, unplaced: list) -> str:
    """The session from top to bottom, then everything that waits to be called beside it.

    `bands` is [(moment, features)] in declared order — this view does not sort, because the order
    IS the finding: it is the order a session runs, read out of the registrations.
    """
    rows = '\n'.join(_bar(moment, features) for moment, features in bands)
    called = ', '.join(sorted(row['name'] for row in on_demand))
    missing = ', '.join(sorted(row['name'] for row in unplaced))
    note = (f'<p class="note"><b>{len(unplaced)} automatic feature'
            f'{"" if len(unplaced) == 1 else "s"} sit on no band at all</b> — nothing in this repo '
            f'declares when {"it fires" if len(unplaced) == 1 else "they fire"}: '
            f'<code>{escape(missing)}</code>.</p>' if unplaced else '')
    return (f'<div class="life">{rows}</div>'
            f'<div class="aside"><h3>on-demand · {len(on_demand)}</h3>'
            f'<p class="q">no moment, by declaration: you call these. Drawn beside the chain '
            f'rather than on it.</p><p class="calls">{escape(called)}</p></div>{note}')


def legend() -> str:
    return ('<p class="note">Every band is read from a registration this repo holds — a harness '
            'settings file, the pre-commit dispatcher\'s own stage order, or the install step that '
            'registers what must live outside the repo. Nothing here is inferred from where a file '
            'sits: that guess put the norms on <code>on save</code> when a norm is loaded with '
            'AGENTS.md at every moment there is. A feature appears on every band it fires at, so '
            'the counts sum to more than the registry — <code>context-chain</code> alone is three.'
            '</p>')
