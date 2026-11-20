# slides_core.py — Google Slides read+write boundary (account-agnostic) for Core/tools/slides/gslides
import pathlib, sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / 'auth'))
from googleapiclient.discovery import build
import gauth

# Two tokens, same split as files/gdrive: reads are cheap, edit-anything is not.
SCOPES = ["https://www.googleapis.com/auth/presentations.readonly"]
SCOPES_WRITE = ["https://www.googleapis.com/auth/presentations"]

# Standard 16:9 deck, in EMU. Every transform below is expressed against these, so a
# caller can place an element by fraction of the slide and never handle the unit.
SLIDE_W, SLIDE_H = 9144000, 5143500


def _read_token(alias: str) -> tuple:
    """Which grant a read should use: the strongest one this alias already has.

    An edit consent strictly contains a read consent, so demanding a second browser trip
    for the subset buys no safety — it just gives the account two tokens that can die
    independently. Aliases that only ever got the read grant are unaffected.
    """
    if (gauth.config_dir("slides-write") / f"{alias}.token.json").exists():
        return "slides-write", SCOPES_WRITE
    return "slides", SCOPES


def get_service(alias: str, write: bool = False):
    service, scopes = ("slides-write", SCOPES_WRITE) if write else _read_token(alias)
    return build("slides", "v1", credentials=gauth.auth(alias, service, scopes))


def get_presentation(alias: str, presentation_id: str, write: bool = False) -> dict:
    """Fetch full presentation JSON from the Slides API."""
    return get_service(alias, write).presentations().get(
        presentationId=presentation_id
    ).execute()


def list_presentations(alias: str, name: str = "") -> list:
    """List presentations from Drive. Optionally filter by name substring."""
    drive_creds = gauth.auth(alias, "drive", ["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=drive_creds)
    q = "mimeType='application/vnd.google-apps.presentation' and trashed=false"
    if name:
        q += f" and name contains '{name}'"
    res = svc.files().list(
        q=q,
        pageSize=100,
        fields="files(id,name,modifiedTime,webViewLink)",
        orderBy="modifiedTime desc",
    ).execute()
    return res.get("files", [])


def create(alias: str, title: str) -> dict:
    """Create an empty presentation and return it."""
    return get_service(alias, write=True).presentations().create(
        body={"title": title}
    ).execute()


def apply(alias: str, presentation_id: str, requests: list) -> dict:
    """The one write path: a list of Slides API requests, applied atomically.

    Every edit this tool makes goes through here. The API is itself a batch of typed
    requests, so wrapping it is honest — inventing a DSL on top would be the thing that
    goes stale when Google adds a request type.
    """
    return get_service(alias, write=True).presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()


def url(presentation_id: str) -> str:
    return f"https://docs.google.com/presentation/d/{presentation_id}/edit"


def textbox(object_id: str, page_id: str, text: str,
            x: float = 0.1, y: float = 0.1, w: float = 0.8, h: float = 0.15) -> list:
    """Requests for one text box, positioned by fraction of the slide."""
    return [
        {"createShape": {
            "objectId": object_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {"width": {"magnitude": SLIDE_W * w, "unit": "EMU"},
                         "height": {"magnitude": SLIDE_H * h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "unit": "EMU",
                              "translateX": SLIDE_W * x, "translateY": SLIDE_H * y},
            },
        }},
        {"insertText": {"objectId": object_id, "text": text}},
    ]


def move(object_id: str, x: float, y: float) -> dict:
    """Absolute reposition, by fraction of the slide. The primitive a motion sequence needs."""
    return {"updatePageElementTransform": {
        "objectId": object_id,
        "applyMode": "ABSOLUTE",
        "transform": {"scaleX": 1, "scaleY": 1, "unit": "EMU",
                      "translateX": SLIDE_W * x, "translateY": SLIDE_H * y},
    }}


def previews(alias: str, presentation_id: str, out_dir: pathlib.Path, dpi: int = 100) -> list:
    """Every slide as `slide_NN_<objectId>.png`: one Drive PDF export, rendered locally.

    Not the Slides thumbnail endpoint: that one is an 'expensive read' with a per-minute
    quota, so a 20+ slide deck gets a 429 halfway. The export is one call for any size.
    """
    import tempfile, shutil
    sys.path.insert(0, str(_HERE.parent / 'files'))
    import deck_sample, drive_core
    ids = [s["objectId"] for s in get_presentation(alias, presentation_id).get("slides", [])]
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        try:
            pdf = drive_core.download_file(alias, presentation_id, pathlib.Path(tmp))
        except Exception as err:  # Drive refuses exports over ~10 MB; a link-shared deck still has the public one
            if "too large" not in str(err):
                raise
            try:
                pdf = deck_sample.download_public_export(presentation_id, pathlib.Path(tmp) / "deck.pdf")
            except RuntimeError:  # over 10 MB and not link-shared: one thumbnail per slide, slow but sure
                return _thumbnails(alias, presentation_id, ids, out_dir)
        pages = deck_sample.render_pages(pdf, pathlib.Path(tmp) / "p", dpi=dpi)
        paths, width = [], max(2, len(str(len(ids))))  # names sort in slide order past 99
        for idx, (sid, page) in enumerate(zip(ids, pages), 1):
            dest = out_dir / f"slide_{idx:0{width}d}_{sid}.png"
            shutil.move(page, dest)  # not Path.replace: /tmp and out_dir are often different filesystems
            paths.append(dest)
    return paths


def _thumbnails(alias: str, presentation_id: str, ids: list, out_dir: pathlib.Path) -> list:
    """The last resort of `previews`: the thumbnail endpoint, waiting out its per-minute quota on 429."""
    import time, urllib.request
    from googleapiclient.errors import HttpError
    svc, paths, width = get_service(alias), [], max(2, len(str(len(ids))))
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, sid in enumerate(ids, 1):
        for wait in (0, 15, 30, 60, 60):
            time.sleep(wait)
            try:
                t = svc.presentations().pages().getThumbnail(
                    presentationId=presentation_id, pageObjectId=sid,
                    thumbnailProperties_thumbnailSize="MEDIUM").execute()
                break
            except HttpError as err:
                if err.resp.status != 429:
                    raise
        else:
            raise RuntimeError(f"thumbnail quota never recovered at slide {idx}")
        dest = out_dir / f"slide_{idx:0{width}d}_{sid}.png"
        urllib.request.urlretrieve(t["contentUrl"], dest)
        paths.append(dest)
    return paths


def contact_sheets(paths: list, out_dir: pathlib.Path, cols: int = 5, rows: int = 4) -> list:
    """20 numbered slides per image: a whole deck seen in a handful of reads, by a person or an agent."""
    from PIL import Image, ImageDraw
    w, h, per, sheets = 400, 225, cols * rows, []
    for k in range(0, len(paths), per):
        sheet = Image.new("RGB", (cols * w, rows * h), "white")
        draw = ImageDraw.Draw(sheet)
        for j, p in enumerate(paths[k:k + per]):
            x, y = (j % cols) * w, (j // cols) * h
            sheet.paste(Image.open(p).convert("RGB").resize((w - 6, h - 6)), (x + 3, y + 3))
            draw.rectangle([x + 3, y + 3, x + 36, y + 21], fill="black")
            draw.text((x + 6, y + 6), str(k + j + 1), fill="yellow")
        sheets.append(out_dir / f"sheet_{k // per + 1:02d}.png")
        sheet.save(sheets[-1])
    return sheets

