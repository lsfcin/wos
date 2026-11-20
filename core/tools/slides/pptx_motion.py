# pptx_motion.py — motion a .pptx carries and a PDF cannot: transitions, click-timed effects, slide links
import re
from lxml import etree

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
P159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
DIM = 0.35  # the context a reveal leaves behind (motion-skills-iart; 0.20 was a guess)

# Easing is where motion gets its meaning: arrive decelerating, leave accelerating, travel symmetric.
# Morph cannot take one — its curve is fixed — so anything whose feel matters is an effect, not a Morph.
EASE = {"out": (0, 100000), "in": (100000, 0), "inout": (50000, 50000), "linear": (0, 0)}


def q(ns, tag):
    return f"{{{ns}}}{tag}"


def _place(slide, el):
    """A transition sits right after clrMapOvr (or cSld) and before timing, or PowerPoint repairs the file."""
    sld = slide._element
    for old in sld.findall(q(MC, "AlternateContent")) + sld.findall(q(P, "transition")):
        sld.remove(old)
    anchor = sld.find(q(P, "clrMapOvr"))
    (anchor if anchor is not None else sld.find(q(P, "cSld"))).addnext(el)


def transition(slide, kind="morph", dur=1000, direction="l", after=None, by="Object"):
    """morph | push | fade | cut. `after` (ms) advances on its own — a rehearsed, narrated deck.
    A Morph pairs by Object, Word or Char: by Char, 'RNN' becomes 'LSTM' reusing its letters."""
    adv = f' advTm="{after}"' if after is not None else ""
    body = {"morph": f'<p159:morph option="by{by}"/>', "push": f'<p:push dir="{direction}"/>',
            "fade": "<p:fade/>", "cut": ""}[kind]
    fallback = "<p:fade/>" if kind == "morph" else body
    req = "p159" if kind == "morph" else "p14"
    _place(slide, etree.fromstring(
        f'<mc:AlternateContent xmlns:mc="{MC}"><mc:Choice xmlns:p159="{P159}" xmlns:p14="{P14}" Requires="{req}">'
        f'<p:transition xmlns:p="{P}" spd="slow" p14:dur="{dur}"{adv}>{body}</p:transition></mc:Choice>'
        f'<mc:Fallback><p:transition xmlns:p="{P}" spd="slow"{adv}>{fallback}</p:transition></mc:Fallback></mc:AlternateContent>'))


def morph_key(shape, key: str):
    """Morph pairs objects across slides by a `!!` name; without it, it guesses — and guesses wrong on repeats."""
    shape.name = "!!" + key
    return shape


# An effect is a dict: target shape id, class, preset, and a builder of its behaviour XML. Timing fields
# (dur, delay, ease, repeat) are shared, so one click staggers its members by delay.

def _fx(shape, cls, preset, body, dur, delay=0, ease="out", repeat=None, sub=0):
    return {"spid": shape.shape_id, "cls": cls, "preset": preset, "sub": sub, "body": body, "dur": dur,
            "delay": delay, "ease": ease, "repeat": repeat, "text": shape.has_text_frame}


def _bhvr(ids, spid, dur, attrs=""):
    names = "".join(f"<p:attrName>{a}</p:attrName>" for a in attrs.split())
    lst = f"<p:attrNameLst>{names}</p:attrNameLst>" if names else ""
    return f'<p:cBhvr><p:cTn id="{next(ids)}" dur="{dur}" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>{lst}</p:cBhvr>'


def _vis(ids, spid, val, delay=0):
    return (f'<p:set><p:cBhvr><p:cTn id="{next(ids)}" dur="1" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="{val}"/></p:to></p:set>')


def appear(shape, **kw):
    return _fx(shape, "entr", 1, lambda i, s, d: _vis(i, s, "visible"), 1, **kw)


def fade_in(shape, dur=400, **kw):
    return _fx(shape, "entr", 10, lambda i, s, d: _vis(i, s, "visible") +
               f'<p:animEffect transition="in" filter="fade">{_bhvr(i, s, d)}</p:animEffect>', dur, **kw)


def fade_out(shape, dur=300, **kw):
    kw.setdefault("ease", "in")
    return _fx(shape, "exit", 10, lambda i, s, d: f'<p:animEffect transition="out" filter="fade">{_bhvr(i, s, d)}</p:animEffect>'
               + _vis(i, s, "hidden", delay=d), dur, **kw)


def wipe_in(shape, dur=600, direction="left", **kw):
    """A line or an arrow drawing itself, opening from `direction`."""
    sub = {"left": 8, "right": 2, "up": 1, "down": 4}[direction]
    return _fx(shape, "entr", 22, lambda i, s, d: _vis(i, s, "visible") +
               f'<p:animEffect transition="in" filter="wipe({direction})">{_bhvr(i, s, d)}</p:animEffect>', dur, sub=sub, **kw)


def grow(shape, pct, dur=600, **kw):
    kw.setdefault("ease", "inout")
    return _fx(shape, "emph", 6, lambda i, s, d: f'<p:animScale>{_bhvr(i, s, d)}<p:by x="{pct * 1000}" y="{pct * 1000}"/></p:animScale>', dur, **kw)


def spin(shape, deg, dur=800, **kw):
    kw.setdefault("ease", "inout")
    return _fx(shape, "emph", 8, lambda i, s, d: f'<p:animRot by="{int(deg * 60000)}">{_bhvr(i, s, d, "r")}</p:animRot>', dur, **kw)


def move(shape, path: str, dur=800, **kw):
    """`path` in slide fractions from where the shape sits — 'M 0 0 L 0.3 0 E', or a Bézier with C. It stays at the end."""
    kw.setdefault("ease", "inout")
    assert re.match(r"M 0 0 ", path) and path.endswith(" E"), "a path starts at the shape (M 0 0) and ends with E"
    return _fx(shape, "path", 0, lambda i, s, d: f'<p:animMotion origin="layout" path="{path}" pathEditMode="relative" ptsTypes="">'
               f'{_bhvr(i, s, d, "ppt_x ppt_y")}</p:animMotion>', dur, **kw)


def dim(shape, to=DIM, **kw):
    """PowerPoint's Transparency emphasis: a held opacity set plus the image filter with the same value.
    It is a step, never a fade — a gradual dim is a Morph to a slide whose fill already carries alpha."""
    return _fx(shape, "emph", 9, lambda i, s, d: f'<p:set>{_bhvr(i, s, "indefinite", "style.opacity")}<p:to><p:strVal val="{to}"/></p:to></p:set>'
               f'<p:animEffect filter="image" prLst="opacity: {to}"><p:cBhvr rctx="IE"><p:cTn id="{next(i)}" dur="indefinite"/>'
               f'<p:tgtEl><p:spTgt spid="{s}"/></p:tgtEl></p:cBhvr></p:animEffect>', 1, **kw)


def timeline(slide, clicks, triggers=None, auto_first=False):
    """clicks: one list of effects per click, played together (stagger with `delay`).
    auto_first: the first group plays on its own once the slide has arrived (PowerPoint's 'After Previous').
    triggers: [(shape, [effects])] played when THAT shape is clicked — the explorable diagram."""
    ids = iter(range(3, 1_000_000))
    built = []

    def par(fx, node):
        acc, dec = EASE[fx["ease"]]
        extra = (f' accel="{acc}"' if acc else "") + (f' decel="{dec}"' if dec else "") + (f' repeatCount="{fx["repeat"]}"' if fx["repeat"] else "")
        built.append(fx)
        return (f'<p:par><p:cTn id="{next(ids)}" presetID="{fx["preset"]}" presetClass="{fx["cls"]}" presetSubtype="{fx["sub"]}"'
                f'{extra} fill="hold" grpId="0" nodeType="{node}"><p:stCondLst><p:cond delay="{fx["delay"]}"/></p:stCondLst>'
                f'<p:childTnLst>{fx["body"](ids, fx["spid"], fx["dur"])}</p:childTnLst></p:cTn></p:par>')

    def group(effects, cond, lead="clickEffect"):
        a, b = next(ids), next(ids)
        inner = "".join(par(fx, lead if k == 0 else "withEffect") for k, fx in enumerate(effects))
        return (f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst>{cond}</p:stCondLst><p:childTnLst>'
                f'<p:par><p:cTn id="{b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{inner}'
                f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')

    click = '<p:cond delay="indefinite"/>'
    auto = click + '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>'  # tn 2 = the main sequence
    main = "".join(group(c, auto, "afterEffect") if k == 0 and auto_first else group(c, click) for k, c in enumerate(clicks))
    seqs = (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{main}</p:childTnLst></p:cTn>'
            f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>') if clicks else ""
    for trig, effects in triggers or []:
        on = f'<p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="{trig.shape_id}"/></p:tgtEl></p:cond>'
        head = next(ids)
        body = group(effects, '<p:cond delay="0"/>')
        seqs += (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{head}" restart="whenNotActive" fill="hold" evtFilter="cancelBubble" nodeType="interactiveSeq">'
                 f'<p:stCondLst>{on}</p:stCondLst><p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync><p:childTnLst>'
                 f'{body}</p:childTnLst></p:cTn><p:nextCondLst>{on}</p:nextCondLst></p:seq>')
    # animBg="1": animate the SHAPE, not only its text. Without it a filled circle with a label shows its
    # fill from the start and only the label fades in (T5: "as bolas ficavam lá sempre aparentes").
    blds = dict.fromkeys(fx["spid"] for fx in built if fx["cls"] in ("entr", "exit") or fx["text"])
    bl = "".join(f'<p:bldP spid="{s}" grpId="0" animBg="1"/>' for s in blds)
    xml = (f'<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
           f'{seqs}</p:childTnLst></p:cTn></p:par></p:tnLst>' + (f"<p:bldLst>{bl}</p:bldLst>" if bl else "") + "</p:timing>")
    sld = slide._element
    for old in sld.findall(q(P, "timing")):
        sld.remove(old)
    ext = sld.find(q(P, "extLst"))
    (ext.addprevious if ext is not None else sld.append)(etree.fromstring(xml))


def link(shape, target):
    """Clicking `shape` jumps to slide `target` — PowerPoint's own link on the shape, so its text keeps its style.
    'Back' is a link to the named slide: online ignores 'last slide viewed' and advances instead (spike S6)."""
    shape.click_action.target_slide = target
    return shape
