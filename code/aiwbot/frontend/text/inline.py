# inline.py — markdown inline spans -> Telegram HTML (bold, strike, code, links, italic).
from __future__ import annotations
import html
import re

# Code spans are stashed under a token before anything else runs, so no other rule can
# rewrite their contents. \x00 can't appear in agent output, so the token is unambiguous.
_CODE_TOKEN = "\x00CODE{}\x00"
_CODE_RE = re.compile(r"`([^`\n]+?)`")
# The lookahead is what keeps `**bold *italic***` from crossing its tags. Without it the
# non-greedy close grabs the FIRST two of the three trailing asterisks, leaving one behind:
# `<b>bold *italic</b>*`, which the italic rule below then closes across the </b> as
# `<b>bold <i>italic</b></i>`. Telegram rejects crossed entities outright, so reply.py's
# fallback strips EVERY tag and the whole message arrives unformatted — one stray construct
# costing the entire answer its bold, code and links. Refusing a close that has another
# asterisk after it makes the match extend to the real boundary instead.
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*(?!\*)")
_STRIKE_RE = re.compile(r"~~(.+?)~~")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((\S+?)\)")
# Both italic forms demand non-word, non-marker neighbours: `**bold**` must survive the
# asterisk rule, and `snake_case_names` must survive the underscore one.
_ITALIC_RE = re.compile(r"(?<![*\w])\*([^*\n]+?)\*(?![*\w])")
_UNDER_RE = re.compile(r"(?<![_\w])_([^_\n]+?)_(?![_\w])")
_SAFE_SCHEMES = ("http://", "https://", "tg://")


def _stash_code(text: str) -> tuple[str, list[str]]:
    """Replace each inline code span with a token, returning the raw bodies to restore later."""
    spans: list[str] = []

    def _take(match: re.Match) -> str:
        body = match.group(1)
        spans.append(body)
        index = len(spans) - 1
        return _CODE_TOKEN.format(index)

    stashed = _CODE_RE.sub(_take, text)
    return stashed, spans


def _restore_code(text: str, spans: list[str]) -> str:
    """Bodies were stashed before escaping, so they get escaped here on the way back in."""
    result = text
    for i, body in enumerate(spans):
        token = _CODE_TOKEN.format(i)
        escaped = html.escape(body, quote=False)
        result = result.replace(token, f"<code>{escaped}</code>")
    return result


def _link(match: re.Match) -> str:
    """[label](url) -> anchor, but only for schemes Telegram will actually open."""
    label = match.group(1)
    url = match.group(2)
    result = match.group(0)
    if url.startswith(_SAFE_SCHEMES):
        # & < > are already escaped by the caller; only the attribute quote is left to handle,
        # and re-running html.escape here would double-escape them.
        href = url.replace('"', "&quot;")
        result = f'<a href="{href}">{label}</a>'
    return result


def convert(text: str) -> str:
    """One line (or run) of inline markdown -> Telegram HTML. Escapes first, so every tag in
    the output is one this function put there. Bold runs before italic or `**x**` gets eaten."""
    stashed, spans = _stash_code(text)
    escaped = html.escape(stashed, quote=False)
    bolded = _BOLD_RE.sub(r"<b>\1</b>", escaped)
    struck = _STRIKE_RE.sub(r"<s>\1</s>", bolded)
    linked = _LINK_RE.sub(_link, struck)
    starred = _ITALIC_RE.sub(r"<i>\1</i>", linked)
    scored = _UNDER_RE.sub(r"<i>\1</i>", starred)
    result = _restore_code(scored, spans)
    return result
