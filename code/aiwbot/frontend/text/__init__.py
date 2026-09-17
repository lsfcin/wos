# __init__.py — facade: agent markdown becomes Telegram HTML. Import text only through here.
from .format import SESSION_ID_LABEL_LEN, clip_chars, format_body, meta_bits, title_words
from .htmlsplit import split_html, strip_tags

__all__ = ["SESSION_ID_LABEL_LEN", "clip_chars", "format_body", "meta_bits", "title_words",
           "split_html", "strip_tags"]
