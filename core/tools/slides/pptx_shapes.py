# pptx_shapes.py — the DrawingML a layout is made of: a filled box, a placeholder, a fixed line of text
from xml.sax.saxutils import escape

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSDECL = f'xmlns:a="{A}" xmlns:p="{P}" xmlns:r="{R}"'
W, H = 12192000, 6858000  # 16:9 in EMU

# Every colour is a THEME SLOT, never a hex: a master's theme decides what the slot is, so one
# layout serves every section colour. Slots this template uses (pptx_theme.SLOTS):
#   accent1 section colour · accent2 text over it · dk1 ink · lt1 page · dk2 muted grey


def _xfrm(x, y, w, h) -> str:
    return f'<a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'


def _run_style(size, color, bold, italic, font) -> str:
    attrs = f' sz="{int(size * 100)}"' + (' b="1"' if bold else ' b="0"') + (' i="1"' if italic else '')
    face = f'<a:latin typeface="{escape(font)}"/>' if font else ''
    return f'<a:defRPr{attrs}><a:solidFill><a:schemeClr val="{color}"/></a:solidFill>{face}</a:defRPr>'


def box(i: int, name: str, x, y, w, h, fill: str = "accent1") -> str:
    """A filled rectangle with no outline — the colour block of a section, split or bar."""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr>{_xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:schemeClr val="{fill}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def placeholder(i: int, name: str, kind: str, idx: int, x, y, w, h, *, size=24, color="dk1",
                bold=False, italic=False, font=None, anchor="t", align="l", sample="") -> str:
    """A slot the slide fills: kind is title | body | pic | ctrTitle | subTitle."""
    ph = f'<p:ph type="{kind}"' + (f' idx="{idx}"' if kind not in ("title", "ctrTitle") else '') + '/>'
    head = (f'<p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr>{ph}</p:nvPr></p:nvSpPr><p:spPr>{_xfrm(x, y, w, h)}</p:spPr>')
    if kind == "pic":
        return f'<p:sp>{head}</p:sp>'
    # No autofit, on purpose: text that does not fit must overflow where lint sees it, not shrink —
    # "quase sempre é melhor mais slides do que letra menor" (Lucas, 2026-09-26).
    body = (f'<p:txBody><a:bodyPr anchor="{anchor}" wrap="square"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle><a:lvl1pPr algn="{align}" marL="0" indent="0"><a:buNone/>'
            f'{_run_style(size, color, bold, italic, font)}</a:lvl1pPr></a:lstStyle>'
            f'<a:p><a:r><a:rPr lang="pt-BR"/><a:t>{escape(sample)}</a:t></a:r></a:p></p:txBody>')
    return f'<p:sp>{head}{body}</p:sp>'


def text(i: int, name: str, x, y, w, h, content: str, *, size=10, color="dk2", font=None, align="l") -> str:
    """A fixed line every slide of the layout carries — the footer's name, say."""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr>{_xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="b" lIns="0" rIns="0"/><a:lstStyle/><a:p><a:pPr algn="{align}"/>'
            f'<a:r><a:rPr lang="pt-BR" sz="{int(size * 100)}"><a:solidFill><a:schemeClr val="{color}"/></a:solidFill>'
            + (f'<a:latin typeface="{escape(font)}"/>' if font else '') +
            f'</a:rPr><a:t>{escape(content)}</a:t></a:r></a:p></p:txBody></p:sp>')


def layout(name: str, shapes: list[str]) -> str:
    """One slide layout: its name is what the Slides layout menu shows."""
    return (f'<p:sldLayout {NSDECL} preserve="1" userDrawn="1"><p:cSld name="{escape(name)}"><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            + "".join(shapes) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
