# slides_outline.py — a deck as navigable text: slide index, element ids, and the words on them
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import slides_geom


def element_text(element: dict) -> str:
    """Concatenate the text runs of one page element. Empty string if it holds none."""
    parts = []
    for item in element.get("shape", {}).get("text", {}).get("textElements", []):
        run = item.get("textRun")
        if run:
            parts.append(run.get("content", ""))
    for row in element.get("table", {}).get("tableRows", []):
        for cell in row.get("tableCells", []):
            for item in cell.get("text", {}).get("textElements", []):
                run = item.get("textRun")
                if run:
                    parts.append(run.get("content", ""))
    return "".join(parts).strip()


def _where(element: dict) -> str:
    """Position and size as fractions of the slide — the same unit the write path takes."""
    x, y, w, h = slides_geom.bounds(element)
    return f"@{x:.2f},{y:.2f} {w:.2f}x{h:.2f}"


def kind(element: dict) -> str:
    if "table" in element:
        return "table"
    if "image" in element:
        return "image"
    if "line" in element:
        return "line"
    if "elementGroup" in element:
        return "group"
    return element.get("shape", {}).get("shapeType", "shape").lower()


def outline(presentation: dict, verbose: bool = False) -> str:
    """Render a presentation as text an agent can navigate and act on.

    Element ids are part of the output on purpose: they are exactly what a batchUpdate
    request needs, so reading a deck hands you the handles for editing it.
    """
    lines = [f"# {presentation.get('title', '(untitled)')}",
             f"  id: {presentation.get('presentationId', '?')}"]
    slides = presentation.get("slides", [])
    lines.append(f"  {len(slides)} slides")
    for i, slide in enumerate(slides, 1):
        lines.append("")
        lines.append(f"## slide {i}   [{slide.get('objectId', '?')}]")
        for element in slide.get("pageElements", []):
            text = element_text(element)
            tag = f"  - {kind(element)} [{element.get('objectId', '?')}] {_where(element)}"
            if text:
                first, *rest = text.splitlines()
                lines.append(f"{tag}  {first}")
                for extra in rest:
                    if extra.strip():
                        lines.append(f"      {extra.strip()}")
            elif verbose:
                lines.append(tag)
    return "\n".join(lines)
