# docs_core.py — Google Docs read+write boundary (account-agnostic) for Core/tools/docs/gdocs
import pathlib, sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / 'auth'))
from googleapiclient.discovery import build
import gauth

# Two tokens, same split as slides/gslides: reads are cheap, edit-anything is not.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
SCOPES_WRITE = ["https://www.googleapis.com/auth/documents"]

# Requests that change how long the body is, and therefore shift every index after them.
# This set is the whole reason `check_order` exists — anything not in it can be batched in
# any order, because it leaves the index space alone.
LENGTH_CHANGING = frozenset({
    "insertText", "deleteContentRange", "insertTable", "insertTableRow",
    "insertTableColumn", "deleteTableRow", "deleteTableColumn", "insertPageBreak",
    "insertSectionBreak", "insertInlineImage", "deleteParagraphBullets",
    "createParagraphBullets", "deletePositionedObject",
})


class IndexOrderError(ValueError):
    """A batch whose length-changing requests run low-to-high. Carries the fix."""


def _read_token(alias: str) -> tuple:
    """Which grant a read should use: the strongest one this alias already has.

    An edit consent strictly contains a read consent, so demanding a second browser trip
    for the subset buys no safety — it just gives the account two tokens that can die
    independently. Aliases that only ever got the read grant are unaffected.
    """
    if (gauth.config_dir("docs-write") / f"{alias}.token.json").exists():
        return "docs-write", SCOPES_WRITE
    return "docs", SCOPES


def get_service(alias: str, write: bool = False):
    service, scopes = ("docs-write", SCOPES_WRITE) if write else _read_token(alias)
    return build("docs", "v1", credentials=gauth.auth(alias, service, scopes))


def get_document(alias: str, document_id: str, write: bool = False) -> dict:
    """Fetch full document JSON from the Docs API."""
    return get_service(alias, write).documents().get(documentId=document_id).execute()


def create(alias: str, title: str) -> dict:
    """Create an empty document and return it."""
    return get_service(alias, write=True).documents().create(body={"title": title}).execute()


def request_index(request: dict) -> int:
    """The body index a request addresses, or -1 when it addresses none.

    Docs spells the same idea four ways depending on the request type, so every caller
    that wants "where does this land" would otherwise re-derive the four spellings.
    """
    for body in request.values():
        if not isinstance(body, dict):
            continue
        for key in ("location", "insertionIndex", "primaryFooterId"):
            spot = body.get(key)
            if isinstance(spot, dict) and "index" in spot:
                return spot["index"]
        for key in ("range", "tableRange", "textRange"):
            span = body.get(key)
            if isinstance(span, dict) and "startIndex" in span:
                return span["startIndex"]
        if isinstance(body.get("endOfSegmentLocation"), dict):
            return -1
    return -1


def check_order(requests: list) -> None:
    """Refuse a batch whose length-changing requests run low index to high.

    THE Docs footgun. batchUpdate applies requests in sequence against a body whose
    indices move as it goes, so an insert at index 10 shifts the insert at index 50 that
    was measured before the batch began. Built back-to-front, every request still
    addresses the text the caller actually read. Built front-to-back, request N+1 lands
    somewhere nobody chose — and the API accepts it, so nothing fails loudly.
    """
    seen = None
    for i, request in enumerate(requests):
        if not LENGTH_CHANGING.intersection(request):
            continue
        index = request_index(request)
        if index < 0:
            continue
        if seen is not None and index > seen[1]:
            raise IndexOrderError(
                f"INDEX ORDER — requests[{seen[0]}] edits index {seen[1]}, then "
                f"requests[{i}] edits index {index}, which is later in the body.\n"
                f"    Every edit shifts the indices after it, so requests[{i}] will not\n"
                f"    land where the document you read said it would.\n"
                f"    Sort length-changing requests HIGHEST index first, then re-run.\n"
                f"    Pass --force only if the indices already account for the shift."
            )
        seen = (i, index)


def descending(requests: list) -> list:
    """The same requests, length-changing ones ordered back-to-front. A stable sort, so
    requests that address no index keep the order the caller wrote them in."""
    return sorted(requests, key=lambda r: -request_index(r))


def apply(alias: str, document_id: str, requests: list,
          revision_id: str = "", force: bool = False) -> dict:
    """The one write path: a list of Docs API requests, applied atomically.

    `revision_id` is the one from the same `get`. Passing it makes the API refuse the
    batch outright if the document moved underneath us, which is the only defence against
    applying indices measured against a version somebody has since edited.
    """
    if not force:
        check_order(requests)
    return get_service(alias, write=True).documents().batchUpdate(
        documentId=document_id, body=batch_body(requests, revision_id)
    ).execute()


def batch_body(requests: list, revision_id: str = "") -> dict:
    """The request body a batchUpdate takes. Separate from `apply` so the guarantee that a
    revision actually reaches `writeControl` is checkable without a network call."""
    body = {"requests": requests}
    if revision_id:
        body["writeControl"] = {"requiredRevisionId": revision_id}
    return body


def url(document_id: str) -> str:
    return f"https://docs.google.com/document/d/{document_id}/edit"


def insert_text(index: int, text: str) -> list:
    """Requests for one run of text at a body index."""
    return [{"insertText": {"location": {"index": index}, "text": text}}]


def replace_all_text(old: str, new: str, match_case: bool = True) -> list:
    """Requests for a whole-document find and replace. Index-free, so it is the one edit
    that never needs the document read first."""
    return [{"replaceAllText": {
        "containsText": {"text": old, "matchCase": match_case},
        "replaceText": new,
    }}]
