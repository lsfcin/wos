# docs_outline.py — a document as navigable text: body indices, structure, and the words on them
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def paragraph_text(element: dict) -> str:
    """Concatenate the text runs of one paragraph. Empty string if it holds none."""
    parts = []
    for item in element.get("paragraph", {}).get("elements", []):
        run = item.get("textRun")
        if run:
            parts.append(run.get("content", ""))
    return "".join(parts).strip()


def style(element: dict) -> str:
    """What the element is, in the vocabulary the write path uses.

    A bullet outranks its named style on purpose: `NORMAL_TEXT` is what almost every list
    item reports, so printing that would hide the one fact that changes how it is edited.
    """
    if "table" in element:
        table = element["table"]
        return f"table {table.get('rows', '?')}x{table.get('columns', '?')}"
    if "tableOfContents" in element:
        return "toc"
    if "sectionBreak" in element:
        return "section-break"
    paragraph = element.get("paragraph", {})
    if "bullet" in paragraph:
        return "bullet"
    return paragraph.get("paragraphStyle", {}).get("namedStyleType", "NORMAL_TEXT")


def _table_text(element: dict) -> str:
    """The first cell with words in it — enough to tell two tables apart in an outline."""
    for row in element.get("table", {}).get("tableRows", []):
        for cell in row.get("tableCells", []):
            for item in cell.get("content", []):
                text = paragraph_text(item)
                if text:
                    return text
    return ""


def outline(document: dict, verbose: bool = False) -> str:
    """Render a document as text an agent can navigate and act on.

    Body indices are part of the output on purpose: they are exactly what a batchUpdate
    request needs, so reading a document hands you the handles for editing it — the same
    contract as `gslides read`, which prints element ids for the same reason.

    THEY GO STALE THE MOMENT YOU EDIT. Slides object ids survive a batchUpdate; these
    numbers do not, because every insert or delete shifts the ones after it. The revision
    printed in the header is the guard: pass it back to `apply` and a document that moved
    underneath you rejects the batch instead of misplacing it.
    """
    content = document.get("body", {}).get("content", [])
    paragraphs = sum(1 for e in content if "paragraph" in e)
    tables = sum(1 for e in content if "table" in e)
    lines = [
        f"# {document.get('title', '(sem título)')}",
        f"  id: {document.get('documentId', '?')}   revision: {document.get('revisionId', '?')}",
        f"  {paragraphs} paragraphs, {tables} tables",
        "",
    ]
    for element in content:
        text = paragraph_text(element) or _table_text(element)
        kind = style(element)
        if not text and not verbose:
            continue
        span = f"[{element.get('startIndex', 0)}-{element.get('endIndex', '?')}]"
        first, *rest = (text or "").splitlines() or [""]
        lines.append(f"{span:<14} {kind:<12} {first}")
        for extra in rest:
            if extra.strip():
                lines.append(f"{'':<27} {extra.strip()}")
    return "\n".join(lines)
