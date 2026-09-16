# notion_lines.py — compact text (**bold**, [label](url)) to the rich_text runs Notion stores
import re

# Notion refuses a text run longer than this, and a rich_text array with more runs than this.
MAX_RUN = 2000
MAX_RUNS = 100

_TOKEN = re.compile(r"\*\*(?P<bold>.+?)\*\*|\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)", re.S)
_PLAIN = {"bold": False, "italic": False, "strikethrough": False,
          "underline": False, "code": False, "color": "default"}


def run(content: str, bold: bool = False, url: str = "") -> dict:
    """One rich_text element. A run carries at most one link and one set of annotations."""
    return {"type": "text",
            "text": {"content": content, "link": {"url": url} if url else None},
            "annotations": dict(_PLAIN, bold=bold)}


def _cut(content: str) -> list:
    """A run over the character cap is refused whole, so cut it rather than lose the write."""
    return [content[i:i + MAX_RUN] for i in range(0, len(content), MAX_RUN)] or [""]


def runs(text: str) -> list:
    """`**bold**` and `[label](url)` become their own runs; the text between them stays plain."""
    out, cursor = [], 0
    for match in _TOKEN.finditer(text):
        if match.start() > cursor:
            out += [run(part) for part in _cut(text[cursor:match.start()])]
        if match.group("bold") is not None:
            out += [run(part, bold=True) for part in _cut(match.group("bold"))]
        else:
            out += [run(part, url=match.group("url")) for part in _cut(match.group("label"))]
        cursor = match.end()
    if cursor < len(text):
        out += [run(part) for part in _cut(text[cursor:])]
    if len(out) > MAX_RUNS:
        raise ValueError(f"{len(out)} runs exceeds Notion's cap of {MAX_RUNS} — split the block")
    return out


def paragraph(text: str) -> dict:
    """The block shape `append` takes for a plain paragraph of this text."""
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": runs(text)}}
