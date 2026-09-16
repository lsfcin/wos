# T1 slides: the geometry a deck reports must be the geometry the write path accepts.
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "slides"))
import slides_core
import slides_geom
import slides_outline


def _element(object_id, x, y, w=0.2, h=0.1, text=None, scale=(1.0, 1.0)):
    el = {
        "objectId": object_id,
        "transform": {"scaleX": scale[0], "scaleY": scale[1], "unit": "EMU",
                      "translateX": slides_geom.SLIDE_W * x,
                      "translateY": slides_geom.SLIDE_H * y},
        "size": {"width": {"magnitude": slides_geom.SLIDE_W * w / scale[0]},
                 "height": {"magnitude": slides_geom.SLIDE_H * h / scale[1]}},
    }
    if text is not None:
        el["shape"] = {"shapeType": "TEXT_BOX",
                       "text": {"textElements": [{"textRun": {"content": text}}]}}
    return el


def test_a_read_position_can_be_handed_straight_back_as_an_edit():
    """Outline and move() share one unit. Anything else makes reading useless for writing."""
    element = _element("box01", 0.25, 0.5)
    x, y, _, _ = slides_geom.bounds(element)
    request = slides_core.move("box01", x, y)["updatePageElementTransform"]
    assert request["transform"]["translateX"] == element["transform"]["translateX"]
    assert request["transform"]["translateY"] == element["transform"]["translateY"]


def test_size_accounts_for_scale_not_just_the_stored_magnitude():
    """Slides stores a base size times a scale; reporting the raw magnitude is a wrong box."""
    _, _, w, h = slides_geom.bounds(_element("box01", 0, 0, w=0.5, h=0.25, scale=(2.0, 0.5)))
    assert round(w, 3) == 0.5
    assert round(h, 3) == 0.25


def test_an_ordinary_api_text_box_is_not_mistaken_for_hidden():
    """A real API-created box comes back near scaleY=0.26. The old 0.4 ghost cut ate content."""
    _, _, _, h = slides_geom.bounds(_element("box01", 0, 0, h=0.15, scale=(2.44, 0.257)))
    assert h > 0.1


def test_rotation_is_read_out_of_the_matrix_not_a_field():
    turned = {"scaleX": 0.0, "shearY": 1.0}
    assert round(slides_geom.rotation_deg(turned)) == 90
    assert slides_geom.rotation_deg({"scaleX": 1.0}) == 0


def test_composing_with_an_identity_parent_changes_nothing():
    child = {"scaleX": 2.0, "scaleY": 3.0, "translateX": 10, "translateY": 20}
    out = slides_geom.compose_transforms({}, child)
    assert (out["scaleX"], out["scaleY"]) == (2.0, 3.0)
    assert (out["translateX"], out["translateY"]) == (10, 20)


def test_the_outline_carries_the_ids_an_edit_needs():
    """Reading a deck has to hand back handles, or the agent has to re-fetch raw JSON to act."""
    deck = {"title": "Aula", "presentationId": "pres1",
            "slides": [{"objectId": "slide1",
                        "pageElements": [_element("title01", 0.1, 0.2, text="Abertura")]}]}
    text = slides_outline.outline(deck)
    assert "slide1" in text
    assert "title01" in text
    assert "Abertura" in text


def test_elements_without_text_stay_out_of_the_way_until_asked_for():
    deck = {"title": "d", "presentationId": "p",
            "slides": [{"objectId": "s1", "pageElements": [_element("ball01", 0.5, 0.5)]}]}
    assert "ball01" not in slides_outline.outline(deck)
    assert "ball01" in slides_outline.outline(deck, verbose=True)


def test_a_textbox_request_places_the_box_where_it_was_asked_to():
    requests = slides_core.textbox("box01", "slide1", "oi", x=0.5, y=0.25, w=0.4, h=0.1)
    transform = requests[0]["createShape"]["elementProperties"]["transform"]
    assert transform["translateX"] == slides_core.SLIDE_W * 0.5
    assert transform["translateY"] == slides_core.SLIDE_H * 0.25
    assert requests[1]["insertText"]["text"] == "oi"


def test_get_thumbnail_url_calls_pages_get_thumbnail(monkeypatch):
    class FakePages:
        def getThumbnail(self, presentationId, pageObjectId, thumbnailProperties_mimeType, thumbnailProperties_thumbnailSize):
            class Req:
                def execute(self):
                    return {"contentUrl": f"https://thumbnail.test/{presentationId}/{pageObjectId}"}
            return Req()

    class FakeService:
        def presentations(self):
            class Pres:
                def pages(self):
                    return FakePages()
            return Pres()

    monkeypatch.setattr(slides_core, "get_service", lambda alias: FakeService())
    url = slides_core.get_thumbnail_url("personal", "deck123", "slide01")
    assert url == "https://thumbnail.test/deck123/slide01"

