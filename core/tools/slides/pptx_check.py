# pptx_check.py — motion read back from a .pptx: lint what a room or a PDF would get wrong, and flatten every click into its own slide
import copy, math, re
from lxml import etree
from pptx_motion import A, P, P159, R, q


def _timing(slide):
    return slide._element.find(q(P, "timing"))


def _target(fx) -> str:
    return fx.find(".//" + q(P, "spTgt")).get("spid")


def _clicks(slide):
    """The main sequence as a list of clicks, each a list of effect nodes (the cTn carrying presetClass)."""
    t = _timing(slide)
    main = None if t is None else t.find(".//" + q(P, "cTn") + "[@nodeType='mainSeq']")
    if main is None:
        return []
    return [step.findall(".//" + q(P, "cTn") + "[@presetClass]") for step in main.find(q(P, "childTnLst"))]


def _path_end(path: str):
    return [float(v) for v in re.findall(r"-?\d*\.?\d+", path)[-2:]]


# PowerPoint online refuses to edit a slide past 200 items and chokes the show well before (round 7 deck A, 2026-09-29).
# Both ceilings are provisional until the round-7 bench (`outputs/.drafts/rodada7/bench.py`) is measured.
MAX_ITEMS, MAX_POINTS = 150, 5000


def budget(slide):
    """(items, points): every drawn object, group children included, and every path point it carries."""
    tree = slide.shapes._spTree
    items = sum(1 for el in tree.iter(q(P, "sp"), q(P, "cxnSp"), q(P, "pic"), q(P, "graphicFrame")))
    return items, sum(1 for _ in tree.iter(q(A, "pt")))


def lint(prs, fonts=None, min_pt=14):
    """'slide N: …' lines. `fonts`: the faces the design system allows; None skips that check.
    Exempt from the size floor: a shape named 'footer…' (10pt by design) and text at alpha 0 (a Morph grows it into view)."""
    W, H = prs.slide_width, prs.slide_height
    out, prev_keys = [], set()
    for n, slide in enumerate(prs.slides, 1):
        say = lambda msg: out.append(f"slide {n}: {msg}")
        items, points = budget(slide)
        if items > MAX_ITEMS or points > MAX_POINTS:
            say(f"{items} items, {points} path points — over {MAX_ITEMS}/{MAX_POINTS}, PowerPoint online stalls: cull what is not seen, fuse what moves together")
        shapes = {s.shape_id: s for s in slide.shapes}
        keys = [s.name for s in slide.shapes if s.name.startswith("!!")]
        for k in sorted({k for k in keys if keys.count(k) > 1}):
            say(f"Morph name {k} used twice — Morph cannot tell them apart")
        morph = slide._element.find(".//" + q(P159, "morph")) is not None
        if morph and n > 1 and not set(keys) & prev_keys:
            say("Morph transition but no !!name shared with the previous slide — nothing is paired")
        prev_keys = set(keys)
        t = _timing(slide)
        if t is not None:
            ids = [c.get("id") for c in t.iter(q(P, "cTn"))]
            if len(ids) != len(set(ids)):
                say("timing node ids repeat — PowerPoint drops the whole sequence")
            blds = {b.get("spid"): b for b in t.iter(q(P, "bldP"))}
            for spid in sorted({tg.get("spid") for tg in t.iter(q(P, "spTgt"))} - {str(i) for i in shapes}):
                say(f"an effect targets shape {spid}, which is not on the slide")
            for click in _clicks(slide):
                durs = {}
                for fx in click:
                    spid = _target(fx)
                    sh, b = shapes.get(int(spid)), blds.get(spid)
                    if fx.get("presetClass") in ("entr", "exit") and sh is not None and sh.has_text_frame and (b is None or b.get("animBg") != "1"):
                        say(f"{sh.name}: entrance without animBg — the fill shows from the start, only the text animates")
                    for tn in fx.findall(".//" + q(P, "cBhvr") + "/" + q(P, "cTn")):
                        if tn.get("dur") not in (None, "1", "indefinite"):
                            durs.setdefault(spid, set()).add(tn.get("dur"))
                    for m in fx.iter(q(P, "animMotion")):
                        if math.hypot(*_path_end(m.get("path"))) > 0.34:
                            say(f"shape {spid} travels over a third of the slide in one move — break it, or change its scale on the way")
                for spid, ds in durs.items():
                    if len(ds) > 1:
                        say(f"shape {spid}: effects on one click last {sorted(ds, key=int)} ms — the move and the scale desync")
        for s in slide.shapes:
            off = s.left is not None and (s.left >= W or s.top >= H or s.left + s.width <= 0 or s.top + s.height <= 0)
            if off and not s.name.startswith("!!"):
                say(f"{s.name} sits entirely off the slide and no Morph carries it in")
            if not s.has_text_frame:
                continue
            for r in (r for p in s.text_frame.paragraphs for r in p.runs):
                unseen = r._r.find(".//" + q(A, "alpha") + "[@val='0']") is not None  # text that only exists for a Morph to grow
                if r.font.size is not None and r.font.size.pt < min_pt and not unseen and not s.name.lstrip("!").lower().startswith("footer"):
                    say(f"{s.name}: '{r.text[:20]}' at {r.font.size.pt:g}pt, below {min_pt}")
                if fonts and r.font.name and r.font.name not in fonts:
                    say(f"{s.name}: face {r.font.name} is not in the design system")
    return out


def _end_state(sp, fx, W, H) -> bool:
    """Apply one effect's END state to a shape element; False means the shape has left."""
    if fx.get("presetClass") == "exit":
        return False
    xfrm = sp.find(".//" + q(A, "xfrm"))
    off, ext = xfrm.find(q(A, "off")), xfrm.find(q(A, "ext"))
    shift = lambda dx, dy: (off.set("x", str(int(int(off.get("x")) + dx))), off.set("y", str(int(int(off.get("y")) + dy))))
    for m in fx.iter(q(P, "animMotion")):
        dx, dy = _path_end(m.get("path"))
        shift(dx * W, dy * H)
    for s in fx.iter(q(P, "animScale")):
        f = int(s.find(q(P, "by")).get("x")) / 100000
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        shift(-cx * (f - 1) / 2, -cy * (f - 1) / 2)
        ext.set("cx", str(int(cx * f))); ext.set("cy", str(int(cy * f)))
    for r in fx.iter(q(P, "animRot")):
        xfrm.set("rot", str(int(xfrm.get("rot", "0")) + int(r.get("by"))))
    for st in fx.iter(q(P, "set")):
        attr = st.find(".//" + q(P, "attrName"))
        if attr is not None and attr.text == "style.opacity":
            alpha = str(int(float(st.find(".//" + q(P, "strVal")).get("val")) * 100000))
            for clr in sp.iter(q(A, "srgbClr"), q(A, "schemeClr")):
                for old in clr.findall(q(A, "alpha")):
                    clr.remove(old)
                etree.SubElement(clr, q(A, "alpha")).set("val", alpha)
    return True


def _duplicate(prs, slide):
    """A new slide on the same layout with a deep copy of `slide`'s background, shapes and the relationships they use."""
    new = prs.slides.add_slide(slide.slide_layout)
    tree = new.shapes._spTree
    for el in list(tree)[2:]:
        tree.remove(el)
    remap = {rid: (new.part.relate_to(rel.target_ref, rel.reltype, is_external=True) if rel.is_external
                   else new.part.relate_to(rel.target_part, rel.reltype))
             for rid, rel in slide.part.rels.items() if not rel.reltype.endswith(("/slideLayout", "/notesSlide"))}
    bg = slide._element.find(q(P, "cSld") + "/" + q(P, "bg"))
    if bg is not None:
        new._element.find(q(P, "cSld")).insert(0, copy.deepcopy(bg))
    for el in list(slide.shapes._spTree)[2:]:
        tree.append(copy.deepcopy(el))
    for el in tree.iter():
        for attr in (q(R, "id"), q(R, "embed"), q(R, "link")):
            if el.get(attr) in remap:
                el.set(attr, remap[el.get(attr)])
    return new


def flatten(prs) -> int:
    """Every click becomes its own slide holding the state after it, so a PDF reads a build as a flipbook
    instead of collapsing it to its end. Slides without effects pass through. Returns the slides added."""
    W, H, ids = prs.slide_width, prs.slide_height, prs.slides._sldIdLst
    added = 0
    for slide in list(prs.slides):
        clicks = _clicks(slide)
        if not clicks:
            continue
        entering = {_target(fx) for step in clicks for fx in step if fx.get("presetClass") == "entr"}
        frames = [slide] + [_duplicate(prs, slide) for _ in clicks]
        for k, frame in enumerate(frames):
            done = [fx for step in clicks[:k] for fx in step]
            els = {el.find(".//" + q(P, "cNvPr")).get("id"): el for el in list(frame.shapes._spTree)[2:]
                   if el.find(".//" + q(P, "cNvPr")) is not None}
            gone = entering - {_target(fx) for fx in done if fx.get("presetClass") == "entr"}
            gone |= {_target(fx) for fx in done if _target(fx) in els and not _end_state(els[_target(fx)], fx, W, H)}
            for spid in gone & set(els):
                els[spid].getparent().remove(els[spid])
            t = _timing(frame)
            if t is not None:
                t.getparent().remove(t)
        # the copies were appended at the end of the deck: move them right after their source
        entry = {prs.part.related_part(e.rId): e for e in ids}
        at = list(ids).index(entry[slide.part])
        for j, frame in enumerate(frames[1:], 1):
            e = entry[frame.part]
            ids.remove(e); ids.insert(at + j, e)
        added += len(frames) - 1
    return added
