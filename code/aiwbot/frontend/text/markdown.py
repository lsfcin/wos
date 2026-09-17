# markdown.py — agent markdown -> Telegram HTML: block level (fences, tables, headings, lists).
from __future__ import annotations
import html
import re
from .inline import convert
from . import table

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_NUMBER_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
_QUOTE_RE = re.compile(r"^>\s?(.*)$")
_RULE_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")

# Telegram has no headings, so hierarchy is carried by weight: # and ## shout, ### and
# deeper are plain bold. Two levels is all a chat bubble can legibly hold.
_CAPS_LEVEL = 2
_HR = "─────"
_BULLETS = ("•", "◦")
_NEST_INDENT = 2


def _heading(match: re.Match) -> str:
    """Uppercasing happens before conversion — after it, .upper() would hit the tag names."""
    hashes = match.group(1)
    body = match.group(2)
    level = len(hashes)
    if level <= _CAPS_LEVEL:
        body = body.upper()
    text = convert(body)
    return f"<b>{text}</b>"


def _bullet(match: re.Match) -> str:
    indent = match.group(1)
    body = match.group(2)
    depth = len(indent) // _NEST_INDENT
    last = len(_BULLETS) - 1
    index = min(depth, last)
    glyph = _BULLETS[index]
    text = convert(body)
    return f"{indent}{glyph}  {text}"


def _numbered(match: re.Match) -> str:
    indent = match.group(1)
    number = match.group(2)
    body = match.group(3)
    text = convert(body)
    return f"{indent}{number}.  {text}"


def _quote(match: re.Match) -> str:
    body = match.group(1)
    text = convert(body)
    return f"<blockquote>{text}</blockquote>"


_LINE_RULES = ((_HEADING_RE, _heading), (_BULLET_RE, _bullet),
               (_NUMBER_RE, _numbered), (_QUOTE_RE, _quote))


def _convert_line(line: str) -> str:
    """First matching block rule wins; anything unmatched is plain inline markdown."""
    result = None
    ruled = _RULE_RE.match(line)
    if ruled:
        result = _HR
    else:
        for pattern, handler in _LINE_RULES:
            hit = pattern.match(line)
            if hit:
                result = handler(hit)
                break
    if result is None:
        result = convert(line)
    return result


def _opens_table(lines: list[str], i: int) -> bool:
    result = False
    if table.is_row(lines[i]) and i + 1 < len(lines):
        result = table.is_separator(lines[i + 1])
    return result


def _format_text_chunk(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if _opens_table(lines, i):
            rendered, i = table.render(lines, i)
            out.append(rendered)
        else:
            converted = _convert_line(lines[i])
            out.append(converted)
            i += 1
    return "\n".join(out)


_FENCE = "```"


def stable_prefix(text: str) -> tuple[str, str]:
    """Split a partially-arrived answer into (settled, unsettled).

    Rendering a prefix never produces BROKEN html — `format_body`'s fence regex needs both
    fences and `inline.convert` only emits balanced tags — but it does produce html that can
    still CHANGE: a half-typed `**bold` renders literal now and flips to bold once the closing
    stars land. So a chunk may only be sealed once nothing in it can change again, which is
    everything up to the last blank line that is not inside an open code fence.

    The fence test is a parity count, not a regex, because an unclosed fence means every
    paragraph break after it is inside a code block and none of them are safe boundaries (F4)."""
    lines = text.split("\n")
    cut = 0
    fences = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith(_FENCE):
            fences += 1
        blank = not line.strip()
        if blank and fences % 2 == 0:
            cut = i + 1
    settled = "\n".join(lines[:cut])
    unsettled = "\n".join(lines[cut:])
    return settled, unsettled


def format_body(text: str) -> str:
    # Telegram has no table syntax at all — pipe-tables become row blocks (see table.py).
    out, last = [], 0
    for m in re.finditer(r"```(?:\w+\n)?(.*?)```", text, flags=re.S):
        chunk = _format_text_chunk(text[last:m.start()])
        out.append(chunk)
        fenced = html.escape(m.group(1))
        out.append(f"<pre>{fenced}</pre>")
        last = m.end()
    tail = _format_text_chunk(text[last:])
    out.append(tail)
    return "".join(out)
