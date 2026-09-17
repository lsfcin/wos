# keyboard.py — inline-keyboard primitives: rows of at most four, framed by the panel's controls.
from __future__ import annotations
from telegram import InlineKeyboardButton

# Telegram divides a row's width evenly between its buttons, so fewer buttons means wider labels.
# Four is the ceiling; rows are allowed to hold fewer and are never padded. The earlier fixed
# five-column grid bought square cells and column alignment at the price of ~8-character labels,
# which truncated model ids — Lucas dropped it 2026-07-23 (SPECS AD-13).
MAX_PER_ROW = 4
NOOP = "noop:"


# Telegram divides a row's width evenly and then TRUNCATES a label that does not fit — it never
# wraps — so the number of buttons in a row is really a choice about how many characters survive.
# Measured on Lucas's phone (2026-07-28), a full-width button holds roughly 30 characters, half
# that at two per row, a third at three. Model ids are short enough to sit four across; a sentence
# the agent wrote as an `ask_user` option is not, and came out as "Coding loca…".
_CHARS_PER_ROW = {4: 7, 3: 9, 2: 14, 1: 30}


def per_row(labels: list[str]) -> int:
    """How many of THESE labels fit on one row without being cut — the WIDEST row that still
    holds the longest label, since a row is only as readable as its worst button. Falls to one
    per row for anything phrase-length, which is what an `ask_user` option usually is."""
    longest = max((len(label) for label in labels), default=0)
    fits = 1
    for count in (MAX_PER_ROW, 3, 2):
        if longest <= _CHARS_PER_ROW[count]:
            fits = count
            break
    return fits


def cell(label: str, data: str | None) -> InlineKeyboardButton:
    """A control. `data=None` means the button is drawn but inert — a page arrow parked at the
    end of its range keeps its slot so the row never changes shape."""
    target = data or NOOP
    return InlineKeyboardButton(label, callback_data=target)


def segment(label: str, selected: bool) -> str:
    """Selected reads `[ BUILD ]`, the rest stay bare. Fixed positions mean only the bracket
    appears to move, which is what gives a plain button row a segmented-control feel (AD-5:
    labels are single-line, so the selection has to be spelled out inside the text)."""
    result = f"[ {label} ]" if selected else label
    return result


def chunk(buttons: list[InlineKeyboardButton], per_row: int = MAX_PER_ROW) -> list[list]:
    """Rows as even as the count allows, never wider than per_row. Filling greedily instead
    would leave a last row of one — five buttons as 4+1 rather than 3+2 — and since width is
    shared inside a row, that lone button would stretch to the full bubble."""
    total = len(buttons)
    count = max(1, -(-total // per_row))
    base, spare = divmod(total, count)
    rows = []
    start = 0
    for index in range(count):
        size = base + 1 if index < spare else base
        row = buttons[start:start + size]
        start += size
        rows.append(row)
    return rows


def framed(opener: InlineKeyboardButton, content: list[InlineKeyboardButton],
           closer: InlineKeyboardButton | None = None,
           tail: list[InlineKeyboardButton] | None = None) -> list[list]:
    """The panel's one layout rule: the first button is always the open/close control and the
    last is always the expand/collapse one, with the content flowing between them. `tail` is a
    row of its own (the pager), which then carries the closer so it stays last."""
    buttons = [opener]
    buttons.extend(content)
    if closer is not None and not tail:
        buttons.append(closer)
    rows = chunk(buttons)
    if tail:
        row = list(tail)
        if closer is not None:
            row.append(closer)
        rows.append(row)
    return rows
