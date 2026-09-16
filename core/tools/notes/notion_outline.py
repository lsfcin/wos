# notion_outline.py — a page as navigable text: block ids, structure, and the words on them
MARKERS = {
    "heading_1": "#", "heading_2": "##", "heading_3": "###",
    "bulleted_list_item": "-", "numbered_list_item": "1.", "quote": ">",
    "callout": "!", "toggle": "▸", "child_page": "📄", "child_database": "🗃",
    "divider": "───", "table_row": "|", "paragraph": ".",
}


def rich_text(items: list) -> str:
    return "".join(item.get("plain_text", "") for item in items or []).strip()


def block_text(block: dict) -> str:
    """The words on one block, whatever shape its own type keeps them in."""
    body = block.get(block.get("type", ""), {})
    if not isinstance(body, dict):
        return ""
    if "rich_text" in body:
        return rich_text(body["rich_text"])
    if "cells" in body:                                   # table_row
        return " | ".join(rich_text(cell) for cell in body["cells"])
    for key in ("title", "expression", "url"):            # child_page, equation, bookmark
        if key in body:
            return str(body[key])
    for holder in ("external", "file"):                   # image, file, video, pdf
        if isinstance(body.get(holder), dict):
            return body[holder].get("url", "")
    return ""


def marker(block: dict) -> str:
    """A type-name marker beats a guess: an unknown block prints what it actually is."""
    kind = block.get("type", "")
    if kind == "to_do":
        return "[x]" if block.get("to_do", {}).get("checked") else "[ ]"
    if kind == "code":
        return "```" + block.get("code", {}).get("language", "")
    return MARKERS.get(kind, kind)


def prop_value(prop: dict) -> str:
    """One property as text. An unmapped type stays silent rather than printing raw JSON."""
    kind = prop.get("type", "")
    value = prop.get(kind)
    if kind in ("title", "rich_text"):
        return rich_text(value or [])
    if kind in ("select", "status"):
        return (value or {}).get("name", "")
    if kind == "multi_select":
        return ", ".join(option.get("name", "") for option in value or [])
    if kind == "date":
        return " → ".join(v for v in [(value or {}).get("start"), (value or {}).get("end")] if v)
    if kind == "people":
        return ", ".join(person.get("name", "?") for person in value or [])
    if kind == "files":
        return ", ".join(item.get("name", "") for item in value or [])
    if kind == "checkbox":
        return "✓" if value else "✗"
    if kind == "relation":
        return f"{len(value or [])} linked"
    if kind in ("number", "url", "email", "phone_number", "created_time", "last_edited_time"):
        return "" if value is None else str(value)
    return ""


def title_of(obj: dict) -> str:
    """A database keeps its title at the top level; a page hides it in a typed property."""
    if obj.get("object") == "database":
        return rich_text(obj.get("title", [])) or "(untitled)"
    for prop in obj.get("properties", {}).values():
        if prop.get("type") == "title":
            return rich_text(prop.get("title", [])) or "(untitled)"
    return "(untitled)"


def properties(obj: dict) -> str:
    """The non-empty properties on one line — a database row carries its meaning here."""
    pairs = [(name, prop_value(prop)) for name, prop in obj.get("properties", {}).items()
             if prop.get("type") != "title"]
    return " · ".join(f"{name}={value}" for name, value in pairs if value)


def _lines(blocks: list, indent: int, verbose: bool) -> list:
    out = []
    for block in blocks:
        text = block_text(block)
        if text or verbose or block.get("type") == "divider":
            out.append(f"{'  ' * indent}[{block.get('id', '?')}] {marker(block)} {text}".rstrip())
        out.extend(_lines(block.get("children", []), indent + 1, verbose))
    return out


def outline(obj: dict, blocks: list, verbose: bool = False) -> str:
    """Render a page as text an agent can navigate and act on.

    Block ids lead every line on purpose: they are what a write path addresses, so reading a
    page hands back the handles for editing it — the same contract as `gslides read`.
    """
    head = [f"# {title_of(obj)}", f"  id: {obj.get('id', '?')}"]
    if obj.get("url"):
        head.append(f"  url: {obj['url']}")
    props = properties(obj)
    if props:
        head.append(f"  {props}")
    return "\n".join(head + [""] + _lines(blocks, 0, verbose))


def row_line(row: dict) -> str:
    """One database entry: what it is called, what it says, and the id to read it by."""
    props = properties(row)
    return f"  {title_of(row)}{'  ·  ' + props if props else ''}  id:{row.get('id', '?')}"
