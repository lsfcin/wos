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


def get_thumbnail_url(alias: str, presentation_id: str, page_object_id: str,
                      size: str = "LARGE") -> str:
    """Fetch the temporary URL for a slide thumbnail (PNG) via the Slides API."""
    svc = get_service(alias)
    res = svc.presentations().pages().getThumbnail(
        presentationId=presentation_id,
        pageObjectId=page_object_id,
        thumbnailProperties_mimeType="PNG",
        thumbnailProperties_thumbnailSize=size,
    ).execute()
    return res.get("contentUrl", "")

