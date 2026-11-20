# slides_style.py — a deck's style read back from its JSON: statistics, the archetype of each slide, and lint
import collections, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from slides_geom import bounds  # (x, y, w, h) as fractions of the slide

EDGE = 0.01  # how far past the edge still reads as flush


def _walk(els):
    for e in els:
        if "elementGroup" in e:
            yield from _walk(e["elementGroup"].get("children", []))
        else:
            yield e


def _hex(color: dict):
    c = (color or {}).get("opaqueColor", color or {})
    if "rgbColor" in c:
        return "#%02X%02X%02X" % tuple(round(c["rgbColor"].get(k, 0) * 255) for k in ("red", "green", "blue"))
    return c.get("themeColor")


def _inherited(pres: dict) -> dict:
    """Placeholder id on a layout/master -> (its first run style, its own parent). A run
    styled `{}` inherits, so size and colour are only knowable by walking this chain."""
    out = {}
    for page in pres.get("layouts", []) + pres.get("masters", []):
        for e in _walk(page.get("pageElements", [])):
            sh = e.get("shape", {})
            runs = [t["textRun"].get("style", {}) for t in sh.get("text", {}).get("textElements", []) if "textRun" in t]
            out[e["objectId"]] = (runs[0] if runs else {}, sh.get("placeholder", {}).get("parentObjectId"))
    return out


def runs(slide: dict, chain: dict):
    """(element, text, effective style) for every non-blank text run on a slide; `chain` is `_inherited(pres)`."""
    for e in _walk(slide.get("pageElements", [])):
        sh = e.get("shape", {})
        parent = sh.get("placeholder", {}).get("parentObjectId")
        for t in sh.get("text", {}).get("textElements", []):
            if "textRun" not in t or not t["textRun"]["content"].strip():
                continue
            style, p = dict(t["textRun"].get("style", {})), parent
            while p in chain:
                inherited, p = chain[p]
                for k, v in inherited.items():
                    style.setdefault(k, v)
            yield e, t["textRun"]["content"], style


def archetype(slide: dict, chain: dict) -> str:
    """One word for what kind of slide this is — the unit a style decision is made on."""
    els = list(_walk(slide.get("pageElements", [])))
    words = sum(len(t.split()) for _, t, _ in runs(slide, chain))
    imgs = [bounds(e) for e in els if "image" in e]
    big = max((w * h for _, _, w, h in imgs), default=0)
    drawn = sum(1 for e in els if "line" in e or (e.get("shape", {}).get("shapeType") not in (None, "TEXT_BOX")))
    formula = [1 for _, _, w, h in imgs if w * h < 0.15 and w > 2.5 * h * 9 / 16]  # wide in real proportions
    if any("video" in e for e in els):
        return "video"
    if big >= 0.6:
        return "full-image"
    if formula:
        return "equation"
    if drawn >= 6:  # before table: a grid drawn as a table inside a diagram is still a diagram
        return "diagram"
    if any("table" in e or "sheetsChart" in e for e in els):
        return "table"
    if imgs:
        return "image+text"
    if words <= 10:
        return "statement"
    return "text"


def stats(pres: dict) -> dict:
    fonts, sizes, colors, kinds = (collections.Counter() for _ in range(4))
    words, types, chain = [], collections.defaultdict(list), _inherited(pres)
    for i, s in enumerate(pres.get("slides", []), 1):
        n = 0
        for e, text, st in runs(s, chain):
            c = len(text.strip())
            fonts[st.get("fontFamily")] += c
            sizes[st.get("fontSize", {}).get("magnitude")] += c
            colors[_hex(st.get("foregroundColor"))] += c
            n += len(text.split())
        words.append(n)
        types[archetype(s, chain)].append(i)
        for e in _walk(s.get("pageElements", [])):
            kinds[next((k for k in ("image", "line", "table", "video") if k in e), "shape")] += 1
    return {"slides": len(words), "fonts": fonts, "sizes": sizes, "colors": colors, "kinds": kinds,
            "words": sorted(words), "types": dict(types)}


def _template(pres: dict) -> list:
    """(box, element) for what the master/layouts draw on every slide themselves: images and
    text that is not a placeholder (logo, author line). A slide's text must stay off these."""
    return [(bounds(e), e) for page in pres.get("masters", []) + pres.get("layouts", [])
            for e in _walk(page.get("pageElements", []))
            if "image" in e or (e.get("shape", {}).get("text") and "placeholder" not in e["shape"])]


def _align(e: dict, parents: dict) -> str:
    """Vertical anchor of a text box, walking the placeholder chain; Slides' default is TOP."""
    while e:
        sh = e.get("shape", {})
        if "contentAlignment" in sh.get("shapeProperties", {}):
            return sh["shapeProperties"]["contentAlignment"]
        e = parents.get(sh.get("placeholder", {}).get("parentObjectId"))
    return "TOP"


def _overlap(a, b) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def lint(pres: dict, min_pt: float = 14) -> list:
    """(slide n, objectId, problem) for what a projector will not forgive: text under
    `min_pt`, text off the slide, text over the template, and footer text off the template's
    footer line (same bottom edge, size and vertical anchor). A source link and anything in the
    footer band are exempt from `min_pt` — they are read on the PDF."""
    tpl, out, chain = _template(pres), [], _inherited(pres)
    parents = {e["objectId"]: e for page in pres.get("layouts", []) + pres.get("masters", [])
               for e in _walk(page.get("pageElements", []))}
    line = next(((b, e) for b, e in tpl if "shape" in e and b[1] > 0.8), None)
    line_pt = line and chain[line[1]["objectId"]][0].get("fontSize", {}).get("magnitude", 99)
    for i, s in enumerate(pres.get("slides", []), 1):
        if s.get("slideProperties", {}).get("isSkipped"):
            continue
        seen = set()
        for e, text, st in runs(s, chain):
            oid, sz = e["objectId"], st.get("fontSize", {}).get("magnitude", 99)
            x, y, w, h = box = bounds(e)
            footer = line is not None and line[0][1] - line[0][3] <= y < sum(line[0][1::2])  # starts on it
            if sz < min_pt and "link" not in st and not footer and (oid, "small") not in seen:
                seen.add((oid, "small")); out.append((i, oid, f"{sz:g}pt: {text.strip()[:40]}"))
            if oid in seen:
                continue
            seen.add(oid)
            if min(x, y) < -EDGE or max(x + w, y + h) > 1 + EDGE:
                out.append((i, oid, f"off the slide: {text.strip()[:40]}"))
            if any(_overlap(box, b) for b, _ in tpl):
                out.append((i, oid, f"over the template: {text.strip()[:40]}"))
            if footer and (abs(y + h - sum(line[0][1::2])) > EDGE / 2 or sz != line_pt
                           or _align(e, parents) != _align(line[1], parents)):
                out.append((i, oid, f"off the footer line: {text.strip()[:40]}"))
    return out
