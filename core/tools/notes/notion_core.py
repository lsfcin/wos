# notion_core.py — Notion REST boundary (workspace-agnostic) for Core/tools/notes/notion
import pathlib, re, sys
import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import notion_auth

API = "https://api.notion.com/v1"
# Notion versions its API by contract, not by "latest": the header is mandatory, and a bump can
# change the shape of a database response. Pinned here, bumped deliberately.
VERSION = "2022-06-28"
PAGE_SIZE = 100
# A sub-page is its own read — recursing into one pulls a whole second document unasked.
LEAF_TYPES = ("child_page", "child_database")
# The id is the END of a hex run, not its start: a name like "Computacao-Grafica-<id>" loses its
# dashes here and donates its own trailing "ca" to the front of the run.
_HEX32 = re.compile(r"[0-9a-fA-F]{32}(?![0-9a-fA-F])")


class ApiRefused(RuntimeError):
    """Notion answered, and the answer was no. Its reason is usually actionable."""


def normalize_id(raw: str) -> str:
    """Bare id, dashed id, or a pasted page URL — all reduce to the uuid the API takes."""
    compact = raw.strip().split("?")[0].split("#")[0].replace("-", "")
    found = _HEX32.findall(compact)
    if not found:
        raise ValueError(f"no Notion id in {raw!r}")
    h = found[-1].lower()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def url(object_id: str) -> str:
    return "https://www.notion.so/" + normalize_id(object_id).replace("-", "")


def _message(response) -> str:
    try:
        return response.json().get("message", response.text)
    except ValueError:
        return response.text


def request(alias: str, method: str, path: str, body: dict | None = None) -> dict:
    """Every call goes through here, so every failure mode has exactly one message."""
    response = requests.request(
        method, f"{API}{path}", timeout=30, json=body,
        headers={"Authorization": f"Bearer {notion_auth.load_token(alias)}",
                 "Notion-Version": VERSION, "Content-Type": "application/json"})
    if response.status_code == 401:
        raise notion_auth.AuthMissing(notion_auth.revoked_text(alias))
    if response.status_code in (403, 404):
        raise notion_auth.NotShared(notion_auth.not_shared_text(alias, path))
    if response.status_code >= 400:
        raise ApiRefused(f"NOTION REFUSED THE REQUEST ({response.status_code}):"
                         f"\n    {_message(response)}")
    return response.json()


def paged(alias: str, method: str, path: str, body: dict | None = None, limit: int = 0) -> list:
    """Notion paginates every list endpoint; a caller that forgets truncates silently at 100."""
    out, cursor = [], None
    while True:
        if method == "POST":
            payload = dict(body or {}, page_size=PAGE_SIZE)
            if cursor:
                payload["start_cursor"] = cursor
            data = request(alias, method, path, payload)
        else:
            query = f"?page_size={PAGE_SIZE}" + (f"&start_cursor={cursor}" if cursor else "")
            data = request(alias, method, path + query)
        out.extend(data.get("results", []))
        cursor = data.get("next_cursor")
        if not (data.get("has_more") and cursor) or (limit and len(out) >= limit):
            return out[:limit] if limit else out


def whoami(alias: str) -> dict:
    """The integration behind the token — the cheapest proof that it is alive."""
    return request(alias, "GET", "/users/me")


def search(alias: str, query: str = "", kind: str = "", limit: int = 25) -> list:
    """What the integration can reach, newest first. An empty query lists all of it."""
    body = {"query": query, "sort": {"direction": "descending", "timestamp": "last_edited_time"}}
    if kind:
        body["filter"] = {"property": "object", "value": kind}
    return paged(alias, "POST", "/search", body, limit)


def fetch(alias: str, ident: str) -> dict:
    """A page or a database — Notion has no single endpoint that takes either id."""
    object_id = normalize_id(ident)
    try:
        return request(alias, "GET", f"/pages/{object_id}")
    except notion_auth.NotShared:
        try:
            return request(alias, "GET", f"/databases/{object_id}")
        except notion_auth.NotShared:
            raise notion_auth.NotShared(notion_auth.not_shared_text(alias, ident)) from None


def blocks(alias: str, block_id: str, depth: int = 3) -> list:
    """A page's content tree, nested children attached under `children`."""
    found = paged(alias, "GET", f"/blocks/{normalize_id(block_id)}/children")
    for block in found:
        if block.get("has_children") and depth > 1 and block.get("type") not in LEAF_TYPES:
            block["children"] = blocks(alias, block["id"], depth - 1)
    return found


def rows(alias: str, database_id: str, limit: int = 50) -> list:
    """A database's entries. Each row is a page, so it carries its own id and properties."""
    return paged(alias, "POST", f"/databases/{normalize_id(database_id)}/query", {}, limit)


def run(main_fn, *also) -> None:
    """Entrypoint wrapper: a token or sharing failure prints its own fix, not a traceback.

    `also` takes the caller's own refusals — a malformed batch is the tool answering, not a crash.
    """
    try:
        main_fn()
    except (notion_auth.AuthMissing, notion_auth.NotShared, ApiRefused, *also) as exc:
        sys.exit(str(exc))
    except requests.RequestException as exc:
        sys.exit(f"NOTION UNREACHABLE: {exc}")
