# notion_write.py — the three writes the Notion API has, planned in full before any one is sent
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import notion_core, notion_lines

OPS = ("update", "append", "delete")


class OpRefused(ValueError):
    """The batch is malformed. Nothing was sent, because nothing is sent until all of it parses."""


def _call(op: dict) -> tuple:
    """One operation, one HTTP call — Notion has no batch endpoint to fold them into."""
    kind = op.get("op")
    if kind == "update":
        body = {k: v for k, v in op.items() if k not in ("op", "block")}
        if not body:
            raise OpRefused(f"update of {op.get('block')!r} names no block type to write")
        return "PATCH", f"/blocks/{notion_core.normalize_id(op['block'])}", body
    if kind == "append":
        body = {"children": op["children"]}
        if op.get("after"):
            body["after"] = notion_core.normalize_id(op["after"])
        return "PATCH", f"/blocks/{notion_core.normalize_id(op['parent'])}/children", body
    if kind == "delete":
        return "DELETE", f"/blocks/{notion_core.normalize_id(op['block'])}", None
    raise OpRefused(f"unknown op {kind!r} — expected one of {', '.join(OPS)}")


def plan(operations: list) -> list:
    """Every call is built before any is sent, so a typo in op 9 cannot land ops 1 through 8."""
    if not isinstance(operations, list):
        raise OpRefused("the file must hold a JSON array of operations")
    try:
        return [_call(op) for op in operations]
    except (KeyError, TypeError) as exc:
        raise OpRefused(f"malformed operation: {exc}") from None


def apply(alias: str, operations: list) -> list:
    return [notion_core.request(alias, method, path, body)
            for method, path, body in plan(operations)]


def load(path: str) -> list:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def text_op(alias: str, block_id: str, text: str) -> dict:
    """A block is updated under its own type key, and only the API knows which — so read first."""
    block = notion_core.normalize_id(block_id)
    kind = notion_core.request(alias, "GET", f"/blocks/{block}")["type"]
    return {"op": "update", "block": block, kind: {"rich_text": notion_lines.runs(text)}}
