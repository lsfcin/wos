# T1 slides: the geometry a deck reports must be the geometry the write path accepts.
import pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "slides"))
import deck_sample, slides_core, slides_geom, slides_outline, slides_style


def _element(object_id, x, y, w=0.2, h=0.1, text=None, scale=(1.0, 1.0)):
    el = {
        "objectId": object_id,
        "transform": {"scaleX": scale[0], "scaleY": scale[1], "unit": "EMU",
                      "translateX": slides_geom.SLIDE_W * x, "translateY": slides_geom.SLIDE_H * y},
        "size": {"width": {"magnitude": slides_geom.SLIDE_W * w / scale[0]},
                 "height": {"magnitude": slides_geom.SLIDE_H * h / scale[1]}},
    }
    if text is not None:
        el["shape"] = {"shapeType": "TEXT_BOX", "text": {"textElements": [{"textRun": {"content": text}}]}}
    return el


def test_a_read_position_can_be_handed_straight_back_as_an_edit():
    element = _element("box01", 0.25, 0.5)
    x, y, _, _ = slides_geom.bounds(element)
    req = slides_core.move("box01", x, y)["updatePageElementTransform"]
    assert req["transform"]["translateX"] == element["transform"]["translateX"]
    assert req["transform"]["translateY"] == element["transform"]["translateY"]


def test_size_accounts_for_scale_not_just_the_stored_magnitude():
    _, _, w, h = slides_geom.bounds(_element("box01", 0, 0, w=0.5, h=0.25, scale=(2.0, 0.5)))
    assert round(w, 3) == 0.5 and round(h, 3) == 0.25


def test_an_ordinary_api_text_box_is_not_mistaken_for_hidden():
    _, _, _, h = slides_geom.bounds(_element("box01", 0, 0, h=0.15, scale=(2.44, 0.257)))
    assert h > 0.1


def test_rotation_is_read_out_of_the_matrix_not_a_field():
    assert round(slides_geom.rotation_deg({"scaleX": 0.0, "shearY": 1.0})) == 90
    assert slides_geom.rotation_deg({"scaleX": 1.0}) == 0


def test_composing_with_an_identity_parent_changes_nothing():
    out = slides_geom.compose_transforms({}, {"scaleX": 2.0, "scaleY": 3.0, "translateX": 10, "translateY": 20})
    assert (out["scaleX"], out["scaleY"]) == (2.0, 3.0) and (out["translateX"], out["translateY"]) == (10, 20)


def test_the_outline_carries_the_ids_an_edit_needs():
    deck = {"title": "Aula", "presentationId": "pres1",
            "slides": [{"objectId": "slide1", "pageElements": [_element("title01", 0.1, 0.2, text="Abertura")]}]}
    text = slides_outline.outline(deck)
    assert "slide1" in text and "title01" in text and "Abertura" in text


def test_elements_without_text_stay_out_of_the_way_until_asked_for():
    deck = {"title": "d", "presentationId": "p",
            "slides": [{"objectId": "s1", "pageElements": [_element("ball01", 0.5, 0.5)]}]}
    assert "ball01" not in slides_outline.outline(deck)
    assert "ball01" in slides_outline.outline(deck, verbose=True)


def test_a_textbox_request_places_the_box_where_it_was_asked_to():
    requests = slides_core.textbox("box01", "slide1", "oi", x=0.5, y=0.25, w=0.4, h=0.1)
    trans = requests[0]["createShape"]["elementProperties"]["transform"]
    assert trans["translateX"] == slides_core.SLIDE_W * 0.5
    assert requests[1]["insertText"]["text"] == "oi"


def test_each_preview_is_named_by_its_slide_and_sorts_in_slide_order(monkeypatch, tmp_path):
    ids = [f"s{i}" for i in range(1, 102)]
    monkeypatch.setattr(slides_core, "get_presentation", lambda a, p: {"slides": [{"objectId": i} for i in ids]})
    sys.path.insert(0, str(pathlib.Path(slides_core.__file__).parent.parent / "files"))
    import drive_core
    monkeypatch.setattr(drive_core, "download_file", lambda a, p, d: d / "deck.pdf")
    def render(pdf, prefix, pages=None, dpi=150):  # the pdf family's leaf, in page order: p-1 … p-101
        for n in range(1, len(ids) + 1):
            pathlib.Path(f"{prefix}-{n}.png").write_text(str(n), encoding="utf-8", newline="\n")
        return [pathlib.Path(f"{prefix}-{n}.png") for n in range(1, len(ids) + 1)]
    monkeypatch.setattr(deck_sample, "render_pages", render)
    paths = slides_core.previews("personal", "deck", tmp_path)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == [p.name for p in paths]
    assert names[9] == "slide_010_s10.png" and (tmp_path / "slide_010_s10.png").read_text(encoding="utf-8") == "10"


def test_parse_slide_target_from_url_and_id(tmp_path):
    url = "https://docs.google.com/presentation/d/1xw1QMYfhase1Su0dlT8bYHlYaLouiPOFT2poTHX0i0k/edit#slide=id.p1"
    parsed = deck_sample.parse_slide_target(url)
    assert parsed["kind"] == "google_slides" and parsed["id"] == "1xw1QMYfhase1Su0dlT8bYHlYaLouiPOFT2poTHX0i0k"
    assert deck_sample.parse_slide_target("1xw1QMYfhase1Su0dlT8bYHlYaLouiPOFT2poTHX0i0k")["kind"] == "google_slides"

    pdf = tmp_path / "aula.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    assert deck_sample.parse_slide_target(str(pdf))["kind"] == "local_pdf"
    pptx = tmp_path / "aula.pptx"
    pptx.write_bytes(b"PK test")
    assert deck_sample.parse_slide_target(str(pptx))["kind"] == "local_pptx"
    assert deck_sample.parse_slide_target("invalid")["kind"] == "unknown"


def test_clean_slide_lines_and_similarity():
    lines = deck_sample.clean_slide_lines(" \nIntro\n14\nLUCAS\nAtencao\n", noise_tokens={"LUCAS"})
    assert lines == ["Intro", "Atencao"]
    assert 0.74 <= deck_sample._lexical_similarity({"a", "b", "c"}, {"a", "b", "c", "d"}) <= 0.76


def test_cluster_and_sample_animations():
    slides = [
        "Abertura\nProf",
        "Atencao\nQ e K",
        "Atencao\nQ e K\nMultiplicacao",
        "Atencao\nQ e K\nMultiplicacao\nSoftmax",
        "Conclusao\nProximos passos",
    ]
    clusters = deck_sample.cluster_and_sample(slides, max_samples=10)
    assert len(clusters) == 3
    assert clusters[1]["slides"] == [2, 3, 4] and clusters[1]["key_slide"] == 4


def test_cluster_and_sample_downsampling():
    slides = [f"Modulo {i}\nConteudo {i}" for i in range(1, 31)]
    clusters = deck_sample.cluster_and_sample(slides, max_samples=10)
    assert len(clusters) == 10 and clusters[0]["slides"] == [1] and clusters[-1]["slides"] == [30]


def test_download_public_export_raises_on_html(monkeypatch, tmp_path):
    class FakeResponse:
        def __init__(self): self.headers = {"Content-Type": "text/html"}
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(deck_sample.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())
    try:
        deck_sample.download_public_export("private_id", tmp_path / "test.pdf")
        assert False, "Should raise"
    except RuntimeError as err:
        assert "Google Slides export returned HTML" in str(err)


def _styled(el, **style):
    el["shape"]["text"]["textElements"][0]["textRun"]["style"] = style
    return el


def _deck(*slides, logo=(0.85, 0.9, 0.15, 0.1)):
    return {"slides": [{"objectId": f"s{i}", "pageElements": els} for i, els in enumerate(slides)],
            "masters": [{"pageElements": [dict(_element("logo1", *logo), image={})]}]}


def test_a_run_styled_empty_takes_its_size_from_the_layout_it_inherits():
    body = _styled(_element("body1", 0.1, 0.3, text="nota"), fontSize={"magnitude": 10})
    body["shape"]["placeholder"] = {"type": "BODY"}
    child = _element("t1", 0.1, 0.3, text="nota")
    child["shape"]["placeholder"] = {"type": "BODY", "parentObjectId": "body1"}
    deck = _deck([child])
    deck["layouts"] = [{"pageElements": [body]}]
    assert [p for _, _, p in slides_style.lint(deck)] == ["10pt: nota"]


def test_lint_names_what_a_room_cannot_read_and_spares_a_source_link():
    small = _styled(_element("small", 0.1, 0.3, text="nota miúda"), fontSize={"magnitude": 10})
    link = _styled(_element("link1", 0.1, 0.8, text="fonte"), fontSize={"magnitude": 8}, link={"url": "x"})
    off = _element("off01", -0.1, 0.1, text="cortado")
    logo = _element("onlogo", 0.8, 0.88, text="por cima")
    problems = {oid: p for _, oid, p in slides_style.lint(_deck([small, link, off, logo]))}
    assert set(problems) == {"small", "off01", "onlogo"}
    assert problems["off01"].startswith("off the slide") and problems["onlogo"].startswith("over the template")


def test_footer_text_sits_on_the_template_footer_line_or_is_named():
    author = _styled(_element("author", 0.6, 0.93, w=0.35, h=0.05, text="lucas"), fontSize={"magnitude": 10})
    author["shape"]["shapeProperties"] = {"contentAlignment": "BOTTOM"}
    def anchor(oid, y, align, pt=10):  # 10pt on purpose: the footer band is exempt from min_pt
        el = _styled(_element(oid, 0.03, y, w=0.3, h=0.05, text="rnn"), fontSize={"magnitude": pt})
        el["shape"]["shapeProperties"] = {"contentAlignment": align}
        return el
    deck = _deck([anchor("onit", 0.93, "BOTTOM"), anchor("middle", 0.93, "MIDDLE"), anchor("higher", 0.91, "BOTTOM"),
                  anchor("bigger", 0.93, "BOTTOM", pt=11)])
    deck["masters"][0]["pageElements"].append(author)
    problems = {oid: p for _, oid, p in slides_style.lint(deck)}
    assert set(problems) == {"middle", "higher", "bigger"} and all(p.startswith("off the footer line") for p in problems.values())


def test_the_archetype_follows_what_fills_the_slide():
    image = lambda oid, *box: dict(_element(oid, *box), image={})
    assert slides_style.archetype({"pageElements": [image("big01", 0, 0, 1, 1)]}, {}) == "full-image"
    assert slides_style.archetype({"pageElements": [image("eq001", 0.1, 0.4, 0.5, 0.1)]}, {}) == "equation"
    assert slides_style.archetype({"pageElements": [_element("t1", 0.3, 0.4, text="motivação")]}, {}) == "statement"
