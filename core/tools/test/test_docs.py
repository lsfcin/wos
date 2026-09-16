# T1 docs: an index a document reports must still mean that place when the edit is applied.
import pytest

import docs_core
import docs_outline


def paragraph(start: int, end: int, text: str, named_style: str = "NORMAL_TEXT") -> dict:
    return {
        "startIndex": start, "endIndex": end,
        "paragraph": {
            "elements": [{"startIndex": start, "endIndex": end,
                          "textRun": {"content": text}}],
            "paragraphStyle": {"namedStyleType": named_style},
        },
    }


DOC = {
    "title": "Ata da Banca",
    "documentId": "1AbCdEf",
    "revisionId": "ALBJ98xyz",
    "body": {"content": [
        {"startIndex": 0, "endIndex": 1, "sectionBreak": {}},
        paragraph(1, 29, "Ata da Banca\n", "TITLE"),
        paragraph(29, 52, "Participantes\n", "HEADING_1"),
        paragraph(52, 141, "Reunião realizada em 12 de agosto.\n"),
        {"startIndex": 141, "endIndex": 199,
         "paragraph": {"elements": [{"textRun": {"content": "Lucas Figueiredo\n"}}],
                       "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                       "bullet": {"listId": "kix.1"}}},
    ]},
}


# ── The index-shift footgun ───────────────────────────────────────────────────

def test_a_batch_that_edits_low_to_high_is_refused():
    """The whole reason this module exists. Inserting at 10 pushes the text at 50 to 60,
    so the second request no longer addresses what the caller read."""
    forward = docs_core.insert_text(10, "primeiro") + docs_core.insert_text(50, "segundo")
    with pytest.raises(docs_core.IndexOrderError):
        docs_core.check_order(forward)


def test_the_same_batch_back_to_front_is_accepted():
    backward = docs_core.insert_text(50, "segundo") + docs_core.insert_text(10, "primeiro")
    docs_core.check_order(backward)


def test_descending_turns_a_rejected_batch_into_an_accepted_one():
    """`descending` is the fix the error message names, so it has to actually produce a
    batch that passes the check that rejected the input."""
    forward = docs_core.insert_text(10, "a") + docs_core.insert_text(50, "b")
    docs_core.check_order(docs_core.descending(forward))


def test_a_style_only_batch_may_run_in_any_order():
    """updateTextStyle changes no length, so nothing after it shifts. Refusing these would
    make the guard fire on batches that were never in danger."""
    styling = [
        {"updateTextStyle": {"range": {"startIndex": 10, "endIndex": 20},
                             "textStyle": {"bold": True}, "fields": "bold"}},
        {"updateTextStyle": {"range": {"startIndex": 50, "endIndex": 60},
                             "textStyle": {"bold": True}, "fields": "bold"}},
    ]
    docs_core.check_order(styling)


def test_a_delete_shifts_indices_the_same_way_an_insert_does():
    forward = [
        {"deleteContentRange": {"range": {"startIndex": 10, "endIndex": 20}}},
        {"deleteContentRange": {"range": {"startIndex": 50, "endIndex": 60}}},
    ]
    with pytest.raises(docs_core.IndexOrderError):
        docs_core.check_order(forward)


def test_the_refusal_names_the_fix_not_just_the_problem():
    """A guard that only says no costs a round trip to work out what to do instead."""
    forward = docs_core.insert_text(10, "a") + docs_core.insert_text(50, "b")
    with pytest.raises(docs_core.IndexOrderError) as caught:
        docs_core.check_order(forward)
    assert "HIGHEST index first" in str(caught.value)


# ── Read hands back the handles that the write path takes ─────────────────────

def test_an_index_read_out_of_the_outline_can_be_handed_straight_back_as_an_edit():
    """The round trip the family exists for: what `read --outline` prints is what
    `apply` accepts, with no translation step in between."""
    text = docs_outline.outline(DOC)
    heading = [ln for ln in text.splitlines() if "Participantes" in ln][0]
    index = int(heading.split("[")[1].split("-")[0])

    request = docs_core.insert_text(index, "novo")[0]
    assert docs_core.request_index(request) == index == 29


def test_the_outline_carries_the_revision_a_safe_write_needs():
    assert "ALBJ98xyz" in docs_outline.outline(DOC)


def test_a_bullet_is_reported_as_a_bullet_not_as_normal_text():
    """Almost every list item stores NORMAL_TEXT, so the named style alone would hide the
    one fact that changes how the paragraph is edited."""
    assert docs_outline.style(DOC["body"]["content"][4]) == "bullet"


def test_headings_keep_their_level():
    assert docs_outline.style(DOC["body"]["content"][2]) == "HEADING_1"


def test_elements_without_text_stay_out_of_the_way_until_asked_for():
    assert "section-break" not in docs_outline.outline(DOC)
    assert "section-break" in docs_outline.outline(DOC, verbose=True)


# ── A document that moved underneath us must reject the batch ─────────────────

def test_a_revision_reaches_writecontrol_so_a_stale_batch_is_refused():
    """Indices are measured against one version. Without this the API happily applies them
    to a later one, which is how an edit lands in the middle of somebody's new paragraph."""
    body = docs_core.batch_body(docs_core.insert_text(1, "oi"), "ALBJ98xyz")
    assert body["writeControl"]["requiredRevisionId"] == "ALBJ98xyz"


def test_no_revision_means_no_writecontrol_key_at_all():
    """An empty requiredRevisionId is not the same as omitting it — the API rejects the
    empty string, so a caller with no revision must send a body without the key."""
    assert "writeControl" not in docs_core.batch_body(docs_core.insert_text(1, "oi"))


def test_a_refusal_reaches_the_operator_as_a_message_not_a_traceback():
    """Found live 2026-08-26: check_order fired correctly and its message — which names
    the fix — came out under sixteen lines of stack. A named refusal exits like one."""
    import gcli

    def refuse():
        raise docs_core.IndexOrderError("HIGHEST index first")

    with pytest.raises(SystemExit) as caught:
        gcli.run(refuse, docs_core.IndexOrderError)
    assert "HIGHEST index first" in str(caught.value.code)


def test_comment_text_is_decoded_before_anyone_reads_it():
    """Drive HTML-escapes comments. In Portuguese that is most anchors, so an undecoded
    one is mojibake in the terminal and a wrong quote back to Lucas."""
    import docs_drive

    decoded = docs_drive._unescaped({
        "content": "a&#231;&#227;o",
        "quotedFileContent": {"value": "Se&#231;&#227;o dois"},
        "replies": [{"content": "cora&#231;&#227;o"}],
    })
    assert decoded["content"] == "ação"
    assert decoded["quotedFileContent"]["value"] == "Seção dois"
    assert decoded["replies"][0]["content"] == "coração"


def test_replace_needs_no_index_and_so_needs_no_document_read():
    request = docs_core.replace_all_text("velho", "novo")[0]
    assert docs_core.request_index(request) == -1
    docs_core.check_order(docs_core.replace_all_text("velho", "novo"))
