# speech.py — an agent's markdown answer -> prose a TTS voice can actually read aloud.
from __future__ import annotations
import html
import re

# The voice reply used to be fed `format.plain(result.text)`, i.e. html.escape — a name trap,
# since `plain` means "safe to put in HTML", the exact opposite of "plain prose". Kokoro was
# therefore handed `&#x27;`, `&amp;`, `##` headings, `**` markers, table pipes and raw URLs,
# and tried to pronounce them. That, not the model, is where most of the bad cadence came from.
_FENCE_RE = re.compile(r"```.*?```", re.S)
_CODE_RE = re.compile(r"`([^`\n]+?)`")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(\S+?\)")
_BARE_URL_RE = re.compile(r"https?://\S+")
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.M)
_BULLET_RE = re.compile(r"^\s*[-*+]\s+", re.M)
_EMPHASIS_RE = re.compile(r"(\*{1,3}|~~|__)")
_TABLE_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)
_RULE_RE = re.compile(r"^\s*(?:[-*_]\s*){3,}$", re.M)
_BLANKS_RE = re.compile(r"\n{2,}")
_SPACES_RE = re.compile(r"[ \t]{2,}")

# Said instead of read out character by character. A spoken answer that references a path is
# better served by naming it than by spelling every slash and dot.
_FENCE_SAID = "trecho de código"
_TABLE_SAID = "tabela"
_LINK_SAID = "link"


def _collapse(text: str) -> str:
    """A sentence per line is fine for a voice; a wall of blank lines is a long dead pause."""
    single = _BLANKS_RE.sub("\n", text)
    spaced = _SPACES_RE.sub(" ", single)
    return spaced.strip()


def _strip_blocks(text: str) -> str:
    """Whole constructs a voice cannot render: code fences, tables, horizontal rules."""
    without_fences = _FENCE_RE.sub(f" {_FENCE_SAID}. ", text)
    without_tables = _TABLE_RE.sub(f"{_TABLE_SAID}.", without_fences)
    return _RULE_RE.sub("", without_tables)


def _strip_inline(text: str) -> str:
    """Inline markers, keeping the words they wrapped."""
    unlinked = _LINK_RE.sub(r"\1", text)
    unurled = _BARE_URL_RE.sub(_LINK_SAID, unlinked)
    uncoded = _CODE_RE.sub(r"\1", unurled)
    unheaded = _HEADING_RE.sub("", uncoded)
    unbulleted = _BULLET_RE.sub("", unheaded)
    return _EMPHASIS_RE.sub("", unbulleted)


def _dedupe_tables(text: str) -> str:
    """A table becomes one `tabela.` however many rows it had — otherwise a ten-row table is
    the word said ten times."""
    pattern = re.compile(rf"(?:{_TABLE_SAID}\.\s*){{2,}}")
    return pattern.sub(f"{_TABLE_SAID}. ", text)


def to_speech(markdown: str) -> str:
    """Markdown answer -> prose for TTS. Entities come back as characters, markers vanish,
    and constructs that have no spoken form are named rather than spelled out."""
    unescaped = html.unescape(markdown)
    blocks = _strip_blocks(unescaped)
    deduped = _dedupe_tables(blocks)
    inline = _strip_inline(deduped)
    return _collapse(inline)
