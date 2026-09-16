# T1 notion write: a batch lands whole or not at all, and a link keeps the name it shows.
import pathlib

import pytest

import notion_lines, notion_write

PAGE_ID = "1a2b3c4d5e6f7081920a1b2c3d4e5f60"
DASHED = "1a2b3c4d-5e6f-7081-920a-1b2c3d4e5f60"

def test_a_malformed_batch_sends_nothing_at_all():
    """The whole batch is built before the first call, so op 3's typo cannot land ops 1 and 2."""
    good = {"op": "delete", "block": PAGE_ID}
    with pytest.raises(notion_write.OpRefused):
        notion_write.plan([good, good, {"op": "destroy", "block": PAGE_ID}])
    # A missing key is the tool answering, not a KeyError escaping into a traceback.
    with pytest.raises(notion_write.OpRefused):
        notion_write.plan([{"op": "append", "parent": PAGE_ID}])
    with pytest.raises(notion_write.OpRefused):
        notion_write.plan({"op": "delete", "block": PAGE_ID})


def test_every_write_addresses_a_block_by_id_not_by_position():
    """Notion's counterpart to the gdocs index rule: ids do not shift, so batch order is free."""
    calls = notion_write.plan([
        {"op": "update", "block": f"https://www.notion.so/x-{PAGE_ID}", "paragraph": {}},
        {"op": "append", "parent": PAGE_ID, "after": DASHED, "children": []},
        {"op": "delete", "block": PAGE_ID},
    ])
    assert [method for method, _, _ in calls] == ["PATCH", "PATCH", "DELETE"]
    assert all(DASHED in path for _, path, _ in calls), "a pasted URL must reduce to the uuid"
    assert calls[1][2]["after"] == DASHED


def test_a_named_link_survives_the_trip_into_rich_text():
    """The AI4Good calendar format: the label is what students click, not a bare URL."""
    runs = notion_lines.runs("12|QUA\t[Apresentação](https://slides/1) | Abertura")
    linked = [r for r in runs if r["text"]["link"]]
    assert len(linked) == 1
    assert linked[0]["text"]["content"] == "Apresentação"
    assert linked[0]["text"]["link"]["url"] == "https://slides/1"
    assert "".join(r["text"]["content"] for r in runs) == "12|QUA\tApresentação | Abertura"


def test_a_run_over_notions_character_cap_is_cut_rather_than_refused():
    runs = notion_lines.runs("x" * (notion_lines.MAX_RUN + 10))
    assert len(runs) == 2 and max(len(r["text"]["content"]) for r in runs) <= notion_lines.MAX_RUN
    with pytest.raises(ValueError):
        notion_lines.runs("**b** " * (notion_lines.MAX_RUNS + 1))
