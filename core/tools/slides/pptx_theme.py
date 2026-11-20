# pptx_theme.py — one theme per section: the stock theme with its colour slots and fonts rewritten
from lxml import etree

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

# What each slot MEANS in a generated template. dk1/lt1 are ink and page even on a dark deck:
# Slides paints text in DARK1 over LIGHT1, so a dark deck swaps the hexes, not the roles.
SLOTS = {"accent1": "section colour", "accent2": "text over the section colour",
         "dk1": "ink", "lt1": "page", "dk2": "muted grey (footer, faded items)"}


def slots(spec: dict, section: dict) -> dict:
    """The hex behind every slot for one section of a spec."""
    n = spec["neutral"]
    return {"accent1": section["color"], "accent2": n[section.get("on", "page")],
            "dk1": n["ink"], "lt1": n["page"], "dk2": n["muted"]}


def rewrite(blob: bytes, name: str, colors: dict, fonts: dict) -> bytes:
    """The stock theme XML with `colors` (slot -> hex) and heading/body fonts put in."""
    t = etree.fromstring(blob)
    t.set("name", name)
    scheme = t.find(".//a:clrScheme", NS)
    scheme.set("name", name)
    for slot, hexv in colors.items():
        el = scheme.find(f"a:{slot}", NS)
        for child in list(el):
            el.remove(child)
        etree.SubElement(el, f"{{{NS['a']}}}srgbClr").set("val", hexv.lstrip("#").upper())
    for tag, key in (("majorFont", "heading"), ("minorFont", "body")):
        t.find(f".//a:{tag}/a:latin", NS).set("typeface", fonts[key])
    return etree.tostring(t, xml_declaration=True, encoding="UTF-8", standalone=True)
