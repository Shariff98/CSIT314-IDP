"""US-28 Search IDPs by keyword."""
from control.search_idp_controller import SearchIDPController


def test_keyword_matches_title_description_tags_and_location(make_idp):
    make_idp("Loft Office", description="Exposed brick")
    make_idp("Family Room", style_tags="Scandinavian")
    make_idp("Small Flat", location="Punggol")
    controller = SearchIDPController()
    assert [i.title for i in controller.search("loft")] == ["Loft Office"]
    assert [i.title for i in controller.search("brick")] == ["Loft Office"]
    assert [i.title for i in controller.search("scandinavian")] == ["Family Room"]
    assert [i.title for i in controller.search("punggol")] == ["Small Flat"]


def test_search_is_case_insensitive_and_trims(make_idp):
    make_idp("Loft Office")
    assert len(SearchIDPController().search("  LOFT ")) == 1


def test_drafts_are_not_found(make_idp):
    make_idp("Secret Loft", published=False)
    assert SearchIDPController().search("loft") == []


def test_no_match_returns_empty_list(make_idp):
    make_idp("Loft Office")
    assert SearchIDPController().search("castle") == []


def test_blank_keyword_returns_all_published_newest_first(make_idp):
    make_idp("Older", created_at="2026-01-01 10:00:00")
    make_idp("Newer", created_at="2026-02-01 10:00:00")
    assert [i.title for i in SearchIDPController().search("")] == ["Newer", "Older"]


def test_results_can_be_sorted_by_views(make_idp):
    quiet, popular = make_idp("Quiet Room"), make_idp("Popular Room")
    for _ in range(3):
        popular.record_view()
    assert [i.title for i in SearchIDPController().search("room", sort="views")] == ["Popular Room", "Quiet Room"]
