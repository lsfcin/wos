# T1 pptx template: every section becomes a master carrying the same layouts, and every colour stays a theme slot.
import io, pathlib, sys

import pytest

pptx = pytest.importorskip("pptx")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "slides"))
import pptx_masters, pptx_shapes

SPEC = {
    "neutral": {"page": "FFFFFF", "ink": "16171B", "muted": "8A8F96"},
    "fonts": {"heading": "Open Sans", "body": "Open Sans", "footer": "Open Sans Light", "mono": "IBM Plex Mono"},
    "cover": {"course": 24, "topic": 48},
    "footer": {"name": "autor · lugar"},
    "sections": [{"name": "um", "color": "E0A526", "on": "ink"}, {"name": "dois", "color": "2F7F79", "on": "page"}],
    "layouts": [{"kind": "cover", "name": "capa"}, {"kind": "section", "name": "seção", "hook": True},
                {"kind": "split", "name": "split", "ratio": 40, "side": "bottom"},
                {"kind": "content", "name": "conteúdo", "bar": "left"}, {"kind": "code", "name": "código"}],
}


def _reopen(spec):
    buf = io.BytesIO()
    pptx_masters.build(spec).save(buf)
    buf.seek(0)
    return pptx.Presentation(buf)


def test_each_section_is_a_master_with_every_layout_in_spec_order():
    prs = _reopen(SPEC)
    names = [[lay.name for lay in m.slide_layouts] for m in prs.slide_masters]
    assert names == [[p["name"] for p in SPEC["layouts"]]] * len(SPEC["sections"])


def test_each_master_theme_holds_its_own_section_colour_and_its_text_colour():
    prs = _reopen(SPEC)
    for master, sec in zip(prs.slide_masters, SPEC["sections"]):
        theme = master.part.part_related_by(pptx.opc.constants.RELATIONSHIP_TYPE.THEME).blob.decode()
        assert f'<a:accent1><a:srgbClr val="{sec["color"]}"/>' in theme
        on = SPEC["neutral"][sec["on"]]
        assert f'<a:accent2><a:srgbClr val="{on}"/>' in theme


def test_master_and_layout_ids_are_unique_and_in_the_reserved_range():
    prs = _reopen(SPEC)
    ids = [int(e.get("id")) for e in prs.part._element.iter() if e.tag.endswith(("}sldMasterId", "}sldLayoutId"))]
    ids += [int(e.get("id")) for m in prs.slide_masters for e in m.part._element.iter() if e.tag.endswith("}sldLayoutId")]
    assert len(set(ids)) == len(SPEC["sections"]) * (1 + len(SPEC["layouts"]))
    assert min(ids) >= pptx_masters.FIRST_ID


def test_no_layout_hardcodes_a_colour_so_one_layout_serves_every_section():
    prs = _reopen(SPEC)
    for lay in prs.slide_masters[1].slide_layouts:
        xml = lay.part.blob.decode()
        assert "srgbClr" not in xml and "schemeClr" in xml


def test_text_never_shrinks_to_fit():
    xml = pptx_shapes.placeholder(2, "body", "body", 1, 0, 0, 10, 10)
    assert "<a:noAutofit/>" in xml and "normAutofit" not in xml


def test_a_split_names_its_colour_side_and_fills_that_share_of_the_slide():
    lay = _reopen(SPEC).slide_masters[0].slide_layouts[2]
    fill = next(s for s in lay.shapes if s.name == "split fill")
    assert fill.top == pptx_shapes.H - fill.height and round(fill.height / pptx_shapes.H, 2) == 0.40


def test_a_preview_sample_exists_for_every_layout_and_every_section_colour():
    prs = _reopen(SPEC)
    assert len(prs.slides) == len(SPEC["layouts"]) + len(SPEC["sections"]) - 1
