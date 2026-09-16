# forms_spec.py — a form written as JSON: compact spec → Forms API batchUpdate requests
from typing import Any

_CHOICE = {"radio": "RADIO", "checkbox": "CHECKBOX", "dropdown": "DROP_DOWN"}


def _choice(item: dict) -> dict:
    options: list[dict[str, Any]] = [{"value": o} for o in item["options"]]
    if item.get("other"):
        options.append({"isOther": True})
    return {"choiceQuestion": {
        "type": _CHOICE[item["type"]],
        "options": options,
        "shuffle": bool(item.get("shuffle")),
    }}


def _question(item: dict) -> dict:
    kind = item["type"]
    if kind in _CHOICE:
        body = _choice(item)
    elif kind == "text":
        body = {"textQuestion": {"paragraph": bool(item.get("paragraph"))}}
    elif kind == "scale":
        body = {"scaleQuestion": {
            "low": item.get("low", 1), "high": item.get("high", 5),
            "lowLabel": item.get("lowLabel", ""), "highLabel": item.get("highLabel", ""),
        }}
    elif kind == "time":
        body = {"timeQuestion": {"duration": bool(item.get("duration"))}}
    elif kind == "date":
        body = {"dateQuestion": {"includeTime": bool(item.get("includeTime")),
                                 "includeYear": bool(item.get("includeYear", True))}}
    else:
        raise ValueError(f"unknown item type: {kind!r}")
    return {"required": bool(item.get("required")), **body}


def _item(item: dict) -> dict:
    """One spec entry → one Forms item. `section` is a page break, not a question."""
    out = {"title": item.get("title", "")}
    if item.get("description"):
        out["description"] = item["description"]
    if item["type"] == "section":
        out["pageBreakItem"] = {}
    elif item["type"] == "note":
        out["textItem"] = {}
    elif item["type"] == "image":
        out["imageItem"] = {"image": {"sourceUri": item["uri"]}}
    else:
        out["questionItem"] = {"question": _question(item)}
    return out


def requests(spec: dict, start_index: int = 0) -> list:
    """Description first (create() could not carry it), then every item in order."""
    out = []
    if spec.get("description"):
        out.append({"updateFormInfo": {
            "info": {"description": spec["description"]},
            "updateMask": "description",
        }})
    for offset, item in enumerate(spec.get("items", [])):
        out.append({"createItem": {
            "item": _item(item),
            "location": {"index": start_index + offset},
        }})
    return out
