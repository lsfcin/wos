# panelmenu.py — the panel's states drawn as keyboards: mode row, dimension menu, value pickers.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import choices, keyboard, labels
from ..session import registry

# Collapsed, the back control eats one of the four slots and the expander another, so two values
# fit; a picker with nothing to expand keeps that slot and shows three.
SLOTS = keyboard.MAX_PER_ROW - 2
# Expanded: three rows of four, minus the back control. The pager, when needed, is a fourth row.
PAGE = keyboard.MAX_PER_ROW * 3 - 1
_OPEN = "+"
_BACK = "‹"
_MORE = "···"
_LESS = "−"
# Double angles for paging, single for going up a level: the back button and the previous-page
# button both sit in the leftmost slot of their row, so identical glyphs would stack vertically
# meaning two different things.
_PREV = "«"
_NEXT = "»"
_ALL = "all"


def _back(target: str) -> InlineKeyboardButton:
    """`‹` walks exactly one level up the menu tree. It used to be an `x` that jumped straight
    back to the mode row, which read as "cancel" rather than "back" — Lucas, 2026-07-23."""
    return keyboard.cell(_BACK, target)


def _cells(values: list[str], current: str | None, dim: str,
           qualify: bool = True) -> list[InlineKeyboardButton]:
    buttons = []
    for value in values:
        short = labels.model_label(value, qualify=qualify) if dim == "m" else value
        label = keyboard.segment(short or value, value == current)
        button = InlineKeyboardButton(label, callback_data=f"p:s:{dim}:{value}")
        buttons.append(button)
    return buttons


def root_markup(scope: str) -> InlineKeyboardMarkup:
    """What every answer and re-anchor carries: the dimensions this scope can change, directly.

    The mode row is gone (Lucas, 2026-07-28): the bot runs build only, so BUILD/PLAN was a
    two-option control with one reachable option. Its `+` opener went with it — it existed to
    open the dimension menu that is now the root itself, so the panel costs one tap where it
    used to cost two."""
    buttons = []
    for key in choices.menu_dims(scope):
        button = InlineKeyboardButton(choices.LABELS[key], callback_data=f"p:d:{key}")
        buttons.append(button)
    rows = keyboard.chunk(buttons)
    return InlineKeyboardMarkup(rows)


def menu_markup(scope: str) -> InlineKeyboardMarkup:
    """The dimension menu IS the root now. Kept as its own name because `p:menu` is a stored
    panel state on messages already in the chat, and a tap on one of those must still resolve."""
    return root_markup(scope)


def _pager(prefix: str, page: int, pages: int) -> list[InlineKeyboardButton]:
    """« N/M » as its own row, so the collapse control can stay the very last button."""
    back = f"{prefix}:{page - 1}" if page > 0 else None
    ahead = f"{prefix}:{page + 1}" if page + 1 < pages else None
    return [keyboard.cell(_PREV, back),
            keyboard.cell(f"{page + 1}/{pages}", None),
            keyboard.cell(_NEXT, ahead)]


def _cut_off(values: list[str], current: str, visible: int | None) -> bool:
    """Would the selection fall outside the slots actually drawn?"""
    result = False
    if visible is not None:
        position = values.index(current)
        result = position >= visible
    return result


def _ordered(values: list[str], current: str | None, prefer: tuple = (),
             visible: int | None = None) -> list[str]:
    """The picker's candidates, selected-first whenever the selection would otherwise fall off
    the cut — including when it came from the drill-down and is not in the shortlist at all. A
    picker that hides what is currently set is worse than one that reorders. With nothing
    selected, `prefer` decides who gets the visible slots; the rest keep their order.

    Hoisting is conditional on `visible` because it used to be unconditional, which reshuffled
    the buttons under Lucas's thumb every single time he picked one — claude's four aliases all
    fit on the row, so there was nothing to rescue and the motion was pure noise (2026-07-27).
    A list that already shows its selection keeps its declared order."""
    if current and current not in values:
        ordered = [current] + values
    elif current and _cut_off(values, current, visible):
        rest = [value for value in values if value != current]
        ordered = [current] + rest
    elif not current and prefer:
        head = [value for value in prefer if value in values]
        tail = [value for value in values if value not in head]
        ordered = head + tail
    else:
        ordered = values
    return ordered


def _paged(prefix: str, values: list[str], current: str | None, dim: str,
           page: int, extra: list) -> list[list]:
    pages = max(1, -(-len(values) // PAGE))
    start = page * PAGE
    shown = values[start:start + PAGE]
    buttons = _cells(shown, current, dim)
    if page + 1 == pages:
        buttons.extend(extra)
    tail = _pager(prefix, page, pages) if pages > 1 else None
    closer = keyboard.cell(_LESS, f"p:d:{dim}")
    return keyboard.framed(_back("p:menu"), buttons, closer, tail)


def values_markup(dim: str, values: list[str], current: str | None, *,
                  expanded: bool = False, page: int = 0, extra: list = ()) -> InlineKeyboardMarkup:
    """One value picker. Collapsed is a single row: `‹`, then two values and `···`, or three
    values when the list fits and there is nothing to expand. Expanded grows to three rows and
    pages past that, with `extra` (the model picker's `all`) on the last page. Preference only
    reorders the collapsed slice — expanded keeps the declared order, which for effort is an
    ordinal ladder and should read as one."""
    if expanded:
        candidates = _ordered(values, current, visible=PAGE)
        rows = _paged(f"p:x:{dim}", candidates, current, dim, page, list(extra))
    else:
        prefer = choices.preferred(dim)
        # How many slots the row will have is decided from `values`, before any reordering, so
        # the reorder can be told what "visible" means without the two defining each other.
        total = len(values) if (current is None or current in values) else len(values) + 1
        deeper = total > SLOTS + 1 or bool(extra)
        slots = SLOTS if deeper else SLOTS + 1
        candidates = _ordered(values, current, prefer, slots)
        shown = candidates[:slots]
        buttons = _cells(shown, current, dim)
        closer = keyboard.cell(_MORE, f"p:x:{dim}:0") if deeper else None
        rows = keyboard.framed(_back("p:menu"), buttons, closer)
    return InlineKeyboardMarkup(rows)


def all_button() -> InlineKeyboardButton:
    """Sits in the expanded model picker: the way out of the shortlist into every provider."""
    return InlineKeyboardButton(_ALL, callback_data="p:g")


def _provider_label(name: str) -> str:
    """Provider ids carry a qualifier nobody reads (`alibaba-coding-plan`, `ollama-cloud`), so
    only the leading word survives — already unique across the six configured here."""
    return name.split("-", 1)[0]


def providers_markup(scope: str) -> InlineKeyboardMarkup:
    """The drill-down's first level: who supplies the key. Nothing to collapse, so no `−`."""
    buttons = []
    for name in choices.groups(scope):
        label = _provider_label(name)
        button = InlineKeyboardButton(label, callback_data=f"p:p:{name}:0")
        buttons.append(button)
    rows = keyboard.framed(_back("p:d:m"), buttons)
    return InlineKeyboardMarkup(rows)


def provider_markup(scope: str, name: str, page: int) -> InlineKeyboardMarkup:
    """One page of a provider's models — openrouter alone holds 339, so this one always pages."""
    models = choices.groups(scope).get(name) or []
    current = registry.setting_for(scope, "model")
    pages = max(1, -(-len(models) // PAGE))
    start = page * PAGE
    shown = models[start:start + PAGE]
    buttons = _cells(shown, current, "m", qualify=False)
    tail = _pager(f"p:p:{name}", page, pages) if pages > 1 else None
    rows = keyboard.framed(_back("p:g"), buttons, None, tail)
    return InlineKeyboardMarkup(rows)
