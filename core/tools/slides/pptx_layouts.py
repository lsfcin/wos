# pptx_layouts.py — every layout kind the template generator knows, as geometry over the shape primitives
import pptx_shapes as S

W, H = S.W, S.H
M = 685800                         # side margin, 0.75 in
FOOT_H = 280000
FOOT_Y = H - 340000 - FOOT_H       # the footer line every layout shares
TYPE = {"display": 54, "title": 36, "statement": 40, "body": 24, "code": 18, "small": 10}


def _ids():
    n = 1
    while True:
        n += 1
        yield n


def _footer(ids, spec, *, on_color=False, anchor=True, accent=False, split=False) -> list[str]:
    """Title-as-anchor on the left, the author's name on the right, both on the footer line.
    `split`: only the anchor sits on the colour; the name stays on the white side."""
    f, t = spec["fonts"], spec["type"]
    color = "accent2" if on_color else ("accent1" if accent else "dk2")
    out = [S.text(next(ids), "footer name", W / 2, FOOT_Y, W / 2 - M, FOOT_H, spec["footer"]["name"],
                  size=t["small"], color="dk2" if split else color, font=f["footer"], align="r")]
    if anchor:
        out.append(S.placeholder(next(ids), "anchor", "title", 0, M, FOOT_Y, W / 2 - M, FOOT_H,
                                 size=t["small"], color=color, font=f["footer"], anchor="b", sample="âncora"))
    return out


def _split_boxes(side: str, r: float):
    """(colour block, neutral block) as (x, y, w, h) for a split with the colour on `side`."""
    if side in ("left", "right"):
        cw = W * r
        color = (0 if side == "left" else W - cw, 0, cw, H)
        neutral = (cw if side == "left" else 0, 0, W - cw, H)
    else:
        ch = H * r
        color = (0, 0 if side == "top" else H - ch, W, ch)
        neutral = (0, ch if side == "top" else 0, W, H - ch)
    return color, neutral


def section(spec, p):
    """Full fill. `photo` (share of the width, right) leaves that side for a picture inserted per slide."""
    i, t = _ids(), spec["type"]
    tw = W * (1 - p.get("photo", 0) / 100) - 2 * M
    shapes = [S.box(next(i), "section fill", 0, 0, W, H),
              S.placeholder(next(i), "title", "title", 0, M, H * .34, tw, H * .26, size=t["display"],
                            color="accent2", bold=True, anchor="b", sample="seção"),
              S.placeholder(next(i), "english", "body", 1, M, H * .61, tw, H * .1, size=t["body"],
                            color="accent2", italic=True, sample="section")]
    if p.get("hook"):
        shapes.append(S.placeholder(next(i), "hook", "pic", 2, W - M - H * .3, M, H * .3, H * .3))
    return shapes + _footer(i, spec, on_color=True, anchor=False)


def split(spec, p):
    i, t = _ids(), spec["type"]
    (cx, cy, cw, ch), (nx, ny, nw, nh) = _split_boxes(p["side"], p["ratio"] / 100)
    return [S.box(next(i), "split fill", cx, cy, cw, ch),
            S.placeholder(next(i), "number", "body", 2, cx + M / 2, cy + ch - H * .3, min(cw - M, W * .3), H * .25,
                          size=t["display"], color="accent2", bold=True, anchor="b", sample="2"),
            S.placeholder(next(i), "title", "title", 0, nx + M / 2, ny + nh * .3, nw - M, nh * .3, size=t["title"],
                          bold=True, anchor="b", sample="subseção"),
            S.placeholder(next(i), "english", "body", 1, nx + M / 2, ny + nh * .62, nw - M, nh * .15, size=t["body"] * .8,
                          italic=True, color="dk2", sample="subsection")] \
        + _footer(i, spec, on_color=p["side"] in ("right", "bottom"), anchor=False)


def content(spec, p):
    i, t = _ids(), spec["type"]
    bar, thick = p.get("bar", "none"), 90000
    boxes = {"left": (0, 0, thick, H), "right": (W - thick, 0, thick, H),
             "top": (0, 0, W, thick), "bottom": (0, H - thick, W, thick)}
    shapes = [S.box(next(i), "bar", *boxes[bar])] if bar in boxes else []
    return shapes + [S.placeholder(next(i), "body", "body", 1, M, M, W - 2 * M, FOOT_Y - M * 1.4, size=t["body"])] \
        + _footer(i, spec, accent=p.get("footer") == "accent")


def statement(spec, p):
    """One sentence. `split` (share of colour on the left) puts it on the colour; `bar` keeps a thick
    left bar; `figure` lifts it to the top, leaving the lower area for a drawing."""
    i, t = _ids(), spec["type"]
    r, bar = p.get("split", 0) / 100, p.get("bar", 0) / 100
    if r:
        cw = W * r
        return [S.box(next(i), "split fill", 0, 0, cw, H),
                S.placeholder(next(i), "statement", "body", 1, M, H * .2, cw - 1.5 * M, H * .55, size=t["statement"],
                              color="accent2", anchor="ctr", sample="uma frase só"),
                S.placeholder(next(i), "aside", "body", 2, cw + M / 2, H * .2, W - cw - 1.5 * M, H * .55,
                              size=t["title"], color="accent1", bold=True, anchor="ctr", sample="termo")] \
            + _footer(i, spec, on_color=True, split=True)
    x0 = W * bar + M if bar else M * 1.5
    shapes = [S.box(next(i), "bar", 0, 0, W * bar, H)] if bar else []
    y, h = (H * .08, H * .24) if p.get("figure") else (H * .25, H * .45)
    return shapes + [S.placeholder(next(i), "statement", "body", 1, x0, y, W - x0 - M * 1.5, h,
                                   size=t["statement"] * (.8 if p.get("figure") else 1),
                                   anchor="t" if p.get("figure") else "ctr", sample="uma frase só")] + _footer(i, spec)


def number(spec, p):
    i, t = _ids(), spec["type"]
    return [S.placeholder(next(i), "number", "body", 2, M, H * .2, W * .35, H * .55, size=t["display"] * 2.6,
                          color="accent1", bold=True, anchor="ctr", sample="4"),
            S.placeholder(next(i), "title", "title", 0, W * .42, H * .2, W * .58 - M, H * .55, size=t["title"] * 1.3,
                          bold=True, anchor="ctr", sample="princípios")] + _footer(i, spec, anchor=False)


def quote(spec, p):
    i, t, f = _ids(), spec["type"], spec["fonts"]
    return [S.placeholder(next(i), "portrait", "pic", 2, 0, H * .25, W * .32, H * .75),
            S.placeholder(next(i), "quote", "body", 1, W * .38, H * .18, W * .62 - M, H * .5, size=t["statement"],
                          italic=True, font=f.get("quote"), anchor="ctr", sample="uma frase dele"),
            S.placeholder(next(i), "author", "body", 3, W * .38, H * .7, W * .62 - M, H * .08, size=t["body"] * .7,
                          color="dk2", sample="autor · cargo")] + _footer(i, spec)


def definition(spec, p):
    i, t, f = _ids(), spec["type"], spec["fonts"]
    return [S.placeholder(next(i), "term", "title", 0, M * 1.5, H * .2, W - 3 * M, H * .15, size=t["title"],
                          bold=True, anchor="b", sample="termo"),
            S.placeholder(next(i), "definition", "body", 1, M * 1.5, H * .38, W - 3 * M, H * .32, size=t["body"] * 1.2,
                          font=f.get("quote"), sample="a definição, com a palavra-chave em destaque"),
            S.placeholder(next(i), "source", "body", 2, M * 1.5, H * .74, W - 3 * M, H * .06, size=t["small"] * 1.4,
                          color="dk2", sample="fonte · autor, ano")] + _footer(i, spec, anchor=False)


def image(spec, p):
    i, t, side = _ids(), spec["type"], p.get("side", "full")
    if side == "full":
        return [S.placeholder(next(i), "image", "pic", 2, 0, 0, W, H),
                S.placeholder(next(i), "caption", "body", 1, M, H * .62, W * .45, H * .18, size=t["title"],
                              color="lt1", bold=True, anchor="b", sample="texto sobre a imagem")] + _footer(i, spec)
    (px, py, pw, ph), (nx, ny, nw, nh) = _split_boxes(side, p.get("ratio", 50) / 100)
    return [S.placeholder(next(i), "image", "pic", 2, px, py, pw, ph),
            S.placeholder(next(i), "text", "body", 1, nx + M / 2, ny + M, nw - M, nh - 2.4 * M, size=t["title"],
                          bold=True, anchor="ctr", sample="o texto não disputa com a imagem")] + _footer(i, spec)


def compare(spec, p):
    i, t = _ids(), spec["type"]
    half, gap = (W - 2 * M - M / 2) / 2, M / 2
    out = []
    for k, x in enumerate((M, M + half + gap)):
        out += [S.placeholder(next(i), f"image {k + 1}", "pic", 2 + k, x, M, half, half * 9 / 16),
                S.placeholder(next(i), f"label {k + 1}", "body", 4 + k, x, M + half * 9 / 16 + M / 4, half, H * .08,
                              size=t["body"], sample=("antes", "depois")[k])]
    return out + _footer(i, spec)


def canvas(spec, p):
    """Nothing but the footer: diagrams that grow slide by slide are drawn here."""
    return _footer(_ids(), spec)


def code(spec, p):
    i, t = _ids(), spec["type"]
    return [S.placeholder(next(i), "code", "body", 1, M, M, W - 2 * M, FOOT_Y - M * 1.4, size=t["code"],
                          font=spec["fonts"]["mono"], sample="def passo():")] + _footer(i, spec)


def cover(spec, p):
    i, c = _ids(), spec["cover"]
    return [S.placeholder(next(i), "course", "subTitle", 1, M * 1.5, H * .3, W - 3 * M, H * .12, size=c["course"],
                          color="dk2", anchor="b", sample="tópicos em ia · ai4good"),
            S.placeholder(next(i), "topic", "ctrTitle", 0, M * 1.5, H * .43, W - 3 * M, H * .25, size=c["topic"],
                          bold=True, sample="redes recorrentes")] + _footer(i, spec, anchor=False)


KINDS = {"cover": cover, "section": section, "split": split, "content": content, "statement": statement,
         "number": number, "quote": quote, "definition": definition, "image": image, "compare": compare,
         "canvas": canvas, "code": code}


def build(spec: dict) -> list[tuple[str, str]]:
    """(name, layout XML) for every layout the spec lists, in order."""
    spec = {**spec, "type": {**TYPE, **spec.get("type", {})}}
    return [(p["name"], S.layout(p["name"], KINDS[p["kind"]](spec, p))) for p in spec["layouts"]]
