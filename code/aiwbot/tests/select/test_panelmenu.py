# test_panelmenu.py — free unit test: panel layout — rows, controls, ordering, paging.
from frontend.select import choices, keyboard, panel, panelmenu
from frontend.session import registry
from ..panelkit import FAVS as _FAVS, labels as _labels, texts as _texts, data as _data



def _states(scope="s1"):
    return [panelmenu.root_markup(scope),
            panelmenu.menu_markup(scope),
            panelmenu.menu_markup(registry.NEW),
            panelmenu.values_markup("m", _FAVS, None, extra=[panelmenu.all_button()]),
            panelmenu.values_markup("m", _FAVS, None, expanded=True),
            panelmenu.providers_markup(scope),
            panelmenu.provider_markup(scope, "big", 0)]

def test_no_row_exceeds_four_buttons(store):
    for markup in _states():
        for row in markup.inline_keyboard:
            assert 1 <= len(row) <= keyboard.MAX_PER_ROW

def test_first_button_opens_or_goes_back_and_last_expands_or_collapses(store):
    """The panel's one layout rule, so the two controls are always where the thumb expects. The
    root is exempt since build-only made it the top level: there is nothing above it to go back
    to, and nothing left to open (2026-07-28)."""
    for markup in _states()[3:]:
        flat = _texts(markup)
        assert flat[0] in ("+", "‹")
    for markup in _states()[3:5]:
        assert _texts(markup)[-1] in ("···", "−")

def test_back_walks_one_level_not_straight_to_the_root(store):
    """`‹` used to be an `x` that jumped to the mode row, which read as cancel, not back."""
    assert _data(panelmenu.values_markup("m", _FAVS, None))[0] == "p:menu"
    assert _data(panelmenu.providers_markup("s1"))[0] == "p:d:m"
    assert _data(panelmenu.provider_markup("s1", "big", 0))[0] == "p:g"

def test_paging_arrows_are_not_the_back_arrow(store):
    """Both live in the leftmost slot of their row, so they must not share a glyph."""
    markup = panelmenu.provider_markup("s1", "big", 1)
    assert _texts(markup)[0] == "‹"
    assert _labels(markup)[-1][0] == "«"

def test_rows_split_evenly_rather_than_greedily(store):
    """Width is shared inside a row, so a greedy 4+1 would stretch the lone button across the
    whole bubble."""
    rows = keyboard.chunk([object()] * 5)
    assert [len(row) for row in rows] == [3, 2]

def test_collapsed_picker_is_always_one_row(store):
    """Four favourites plus an `all` escape still collapse to a single row — everything past
    the first three lives behind `···`."""
    markup = panelmenu.values_markup("m", _FAVS, None, extra=[panelmenu.all_button()])
    assert len(markup.inline_keyboard) == 1
    assert _texts(markup)[0] == "‹"
    assert _texts(markup)[-1] == "···"

def test_collapsed_picker_that_fits_shows_three_and_no_expander(store):
    markup = panelmenu.values_markup("e", ["low", "high", "max"], "high")
    assert "···" not in _texts(markup)
    assert "[ high ]" in _texts(markup)
    assert len(markup.inline_keyboard[0]) == keyboard.MAX_PER_ROW

def test_the_selected_value_is_never_cut_off(store):
    """Collapsed shows two of five, so the selection is pinned first — a picker that hides what
    is currently set is worse than one that reorders."""
    markup = panelmenu.values_markup("e", ["low", "medium", "high", "xhigh", "max"], "max")
    assert "[ max ]" in _texts(markup)

def test_a_value_chosen_in_the_drill_down_still_shows_in_the_shortlist(store):
    """openrouter/... is not among the favourites, but it is what is set, so it leads the row."""
    markup = panelmenu.values_markup("m", _FAVS, "big/m7", extra=[panelmenu.all_button()])
    assert "[ bi·m7 ]" in _texts(markup)


def test_effort_shows_the_two_values_actually_used(store):
    """Lucas: "medium e high, raramente uso low". By name, since opencode's vocabularies are
    irregular and any positional rule would pick something different on each model."""
    ladder = ["low", "medium", "high", "xhigh", "max"]
    collapsed = _texts(panelmenu.values_markup("e", ladder, None))
    assert collapsed[1:3] == ["medium", "high"]


def test_the_expanded_effort_ladder_keeps_its_ordinal_order(store):
    ladder = ["low", "medium", "high", "xhigh", "max"]
    expanded = _texts(panelmenu.values_markup("e", ladder, None, expanded=True))
    assert expanded[1:6] == ladder

def test_expander_and_collapser_are_both_the_last_button(store):
    collapsed = panelmenu.values_markup("m", _FAVS, None)
    expanded = panelmenu.values_markup("m", _FAVS, None, expanded=True)
    assert _texts(collapsed)[-1] == "···"
    assert _texts(expanded)[-1] == "−"

def test_all_escape_rides_the_last_page_only(store):
    extra = [panelmenu.all_button()]
    values = [f"m{i}" for i in range(30)]
    first = _texts(panelmenu.values_markup("m", values, None, expanded=True, page=0, extra=extra))
    last = _texts(panelmenu.values_markup("m", values, None, expanded=True, page=2, extra=extra))
    assert "all" not in first
    assert "all" in last

def test_pager_is_its_own_row(store):
    markup = panelmenu.provider_markup("s1", "big", 1)
    assert _labels(markup)[-1] == ["«", "2/2", "»"]

def test_arrows_park_at_the_ends_of_the_range(store):
    first = _data(panelmenu.provider_markup("s1", "big", 0))
    last = _data(panelmenu.provider_markup("s1", "big", 1))
    assert "p:p:big:1" in first
    assert "p:p:big:-1" not in first
    assert "p:p:big:2" not in last

def test_callback_data_never_spends_bytes_on_the_scope(store):
    """The keyboard always sits on a message the bot remembers, so the scope is resolved from
    the message id and all 64 bytes stay available for values."""
    markup = panelmenu.provider_markup("s1", "big", 0)
    for value in _data(markup):
        assert "s1" not in value
        assert len(value.encode()) <= 64

def test_provider_labels_drop_the_qualifier_nobody_reads(store):
    assert panelmenu._provider_label("alibaba-coding-plan") == "alibaba"
    assert panelmenu._provider_label("nvidia") == "nvidia"
